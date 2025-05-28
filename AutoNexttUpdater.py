import requests
import sys
import os
import shutil
import time
import hashlib
import ctypes
import subprocess
from pathlib import Path

def verificar_hash(arquivo: str, hash_esperado: str) -> bool:
    """Verifica a integridade do arquivo baixado"""
    sha256 = hashlib.sha256()
    with open(arquivo, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest() == hash_esperado

def executar_como_admin(caminho_exe: str):
    """Tenta executar o programa como administrador"""
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", caminho_exe, None, None, 1)
        return True
    except Exception:
        return False

def atualizar(url_novo_exe: str, hash_esperado: str, max_tentativas=3):
    try:
        caminho_atual = sys.argv[0]
        pasta_atual = os.path.dirname(caminho_atual)
        nome_exe = os.path.basename(caminho_atual)
        caminho_temp = os.path.join(pasta_atual, f"{nome_exe}.temp")
        caminho_backup = os.path.join(pasta_atual, f"{nome_exe}.bak")

        # Tentar várias vezes em caso de falha de rede
        for tentativa in range(max_tentativas):
            try:
                print(f"Baixando nova versão (tentativa {tentativa + 1})...")
                with requests.get(url_novo_exe, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    with open(caminho_temp, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                
                # Verificar integridade do arquivo
                if not verificar_hash(caminho_temp, hash_esperado):
                    raise ValueError("Hash de verificação falhou - arquivo corrompido ou modificado")
                
                break  # Se chegou aqui, download foi bem sucedido
            except Exception as e:
                if tentativa == max_tentativas - 1:
                    raise
                time.sleep(5)  # Espera antes de tentar novamente
                continue

        # Fechar a instância atual se ainda estiver em execução
        print("Finalizando instância atual...")
        time.sleep(2)  # Dar tempo para o programa encerrar

        # Criar backup do arquivo atual
        if os.path.exists(caminho_atual):
            shutil.copy2(caminho_atual, caminho_backup)

        # Substituir o arquivo
        print("Substituindo executável...")
        os.replace(caminho_temp, caminho_atual)

        # Tentar executar o novo arquivo
        print("Iniciando nova versão...")
        try:
            subprocess.Popen([caminho_atual], shell=True)
        except Exception:
            # Se falhar, tentar como admin
            if not executar_como_admin(caminho_atual):
                raise

        sys.exit(0)

    except Exception as e:
        print(f"Erro na atualização: {e}")
        # Tentar restaurar o backup se existir
        if os.path.exists(caminho_backup):
            print("Restaurando versão anterior...")
            os.replace(caminho_backup, caminho_atual)
        sys.exit(1)