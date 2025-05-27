import requests
import sys
import os
import shutil
import time

def baixar_arquivo(url, destino):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(destino, 'wb') as f:
            shutil.copyfileobj(r.raw, f)

def main():
    if len(sys.argv) != 4:
        print("Uso: AutoNexttUpdater.exe <URL_DO_NOVO_EXE> <CAMINHO_DO_ATUAL_EXE> <NOME_NOVO_EXE>")
        sys.exit(1)

    url_novo_exe = sys.argv[1]
    caminho_atual_exe = sys.argv[2]
    nome_arquivo_novo = sys.argv[3]

    print("Aguardando o programa atual encerrar...")
    time.sleep(2)  # Dá tempo para o programa fechar

    nome_temp = nome_arquivo_novo + "_novo.exe"

    try:
        print("Baixando nova versão...")
        baixar_arquivo(url_novo_exe, nome_temp)

        print("Substituindo arquivos...")
        if os.path.exists(caminho_atual_exe):
            os.remove(caminho_atual_exe)
        os.rename(nome_temp, caminho_atual_exe)

        print("Atualização concluída!")

        # Relançar o programa atualizado
        os.startfile(caminho_atual_exe)

    except Exception as e:
        print(f"Erro na atualização: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
