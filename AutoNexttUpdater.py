import requests
import sys
import os
import shutil
import time
import hashlib
import ctypes
import subprocess
import psutil


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


def aguardar_encerramento_arquivo(caminho_arquivo, timeout=60):
    """Aguarda até que nenhum processo esteja usando o arquivo"""
    print(f"Aguardando {os.path.basename(caminho_arquivo)} encerrar...")

    inicio = time.time()
    while time.time() - inicio < timeout:
        if not arquivo_em_uso(caminho_arquivo):
            print("Arquivo liberado.")
            return True
        time.sleep(1)

    print("Tempo limite atingido esperando arquivo liberar.")
    return False


def arquivo_em_uso(caminho_arquivo):
    """Verifica se o arquivo está sendo usado por algum processo"""
    for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
        try:
            if not proc.is_running():
                continue
            if proc.exe() and os.path.samefile(proc.exe(), caminho_arquivo):
                return True
            if proc.cmdline() and caminho_arquivo in proc.cmdline():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False


def atualizar(caminho_alvo: str, url_novo_exe: str, hash_esperado: str, max_tentativas=3):
    try:
        pasta_alvo = os.path.dirname(caminho_alvo)
        nome_arquivo = os.path.basename(caminho_alvo)
        caminho_temp = os.path.join(pasta_alvo, f"{nome_arquivo}.temp")
        caminho_backup = os.path.join(pasta_alvo, f"{nome_arquivo}.bak")

        if not aguardar_encerramento_arquivo(caminho_alvo):
            raise RuntimeError("O arquivo não foi encerrado. Atualização abortada.")

        # Download
        for tentativa in range(max_tentativas):
            try:
                print(f"Baixando nova versão (tentativa {tentativa + 1})...")
                with requests.get(url_novo_exe, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    with open(caminho_temp, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                if not verificar_hash(caminho_temp, hash_esperado):
                    raise ValueError("Hash de verificação falhou - arquivo corrompido ou modificado")

                break
            except Exception as e:
                if tentativa == max_tentativas - 1:
                    raise
                print(f"Erro: {e}. Tentando novamente em 5 segundos...")
                time.sleep(5)
                continue

        # Backup
        if os.path.exists(caminho_alvo):
            shutil.copy2(caminho_alvo, caminho_backup)

        # Substituir
        print("Substituindo executável...")
        os.replace(caminho_temp, caminho_alvo)

        # Relançar
        print("Iniciando nova versão...")
        try:
            subprocess.Popen([caminho_alvo], shell=True)
        except Exception:
            if not executar_como_admin(caminho_alvo):
                raise

        sys.exit(0)

    except Exception as e:
        print(f"Erro na atualização: {e}")
        if os.path.exists(caminho_backup):
            print("Restaurando versão anterior...")
            os.replace(caminho_backup, caminho_alvo)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: atualizador.exe <caminho_do_arquivo_alvo> <url_novo_exe> <hash_esperado>")
        sys.exit(1)

    caminho_alvo = sys.argv[1]
    url_novo_exe = sys.argv[2]
    hash_esperado = sys.argv[3]

    atualizar(caminho_alvo, url_novo_exe, hash_esperado)
