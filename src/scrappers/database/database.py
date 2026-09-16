import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def obter_conexao():
    return psycopg2.connect(DATABASE_URL,connect_timeout=10)

def validar_oferta(conn,id_produto: str, preco: float, desconto: int, plataforma: str = 'amazon') -> bool:
    cursor = None
    try:
        cursor = conn.cursor()
        # 1. Consulta histórico no Neon
        query_busca = """
            SELECT preco, atualizado_em 
            FROM produtos_enviados 
            WHERE id_produto = %s AND plataforma = %s;
        """
        cursor.execute(query_busca, (id_produto, plataforma))
        registro = cursor.fetchone()

        deve_enviar = False

        # Regra 1: Produto inédito
        if not registro:
            deve_enviar = True
        else:
            preco_banco, atualizado_em = registro
            preco_banco = float(preco_banco)
            dias_desde_envio = (datetime.now() - atualizado_em).days

            # Regra 2: Queda de preço em relação ao banco
            if preco < preco_banco:
                deve_enviar = True
            # Regra 3: Reenvio de Super Oferta (>= 50% OFF) após 7 dias
            elif desconto >= 50 and dias_desde_envio >= 7:
                deve_enviar = True

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Erro no banco: {e}")
        raise e
    finally:
        if cursor:
            cursor.close()
    return deve_enviar

def salvar_oferta(conn,id_produto: str, nome: str, preco: float, desconto: int, plataforma: str = 'amazon'):
    cursor = None
    try:
        cursor = conn.cursor()
        query_upsert = """
            INSERT INTO produtos_enviados (id_produto, plataforma, nome, preco, desconto, atualizado_em)
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON CONFLICT (id_produto, plataforma) 
            DO UPDATE SET 
                preco = EXCLUDED.preco, 
                desconto = EXCLUDED.desconto, 
                atualizado_em = NOW();
            """
        cursor.execute(query_upsert, (id_produto, plataforma, nome, preco, desconto))
        conn.commit()
    except Exception as e:
            if conn:
                conn.rollback()
            print(f"Erro no banco: {e}")
            raise e
    finally:
        if cursor:
            cursor.close()

def limpar_produtos_antigos():
    """Remove do banco todos os produtos registrados há mais de 30 dias."""
    conn = None
    try:
        conn = obter_conexao()
        cursor = conn.cursor()
        
        # Deleta registros cuja coluna atualizado_em seja menor que a data atual menos 30 dias
        query = """
            DELETE FROM produtos_enviados
            WHERE atualizado_em < NOW() - INTERVAL '30 days';
        """
        cursor.execute(query)
        conn.commit()
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Erro no banco: {e}")
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()