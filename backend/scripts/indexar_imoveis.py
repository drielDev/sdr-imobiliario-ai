from pathlib import Path
import sys
import shutil
import argparse


BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from app.catalogo.rag import ImovelRAG
from app.catalogo.models import FiltroImovel


def limpar_base_vetorial():

	db_path = BASE_DIR / "chroma_db"
	if db_path.exists():
		shutil.rmtree(db_path)


def executar_pipeline(reindexar: bool = False, validar: bool = True):

	print("[1/4] Iniciando pipeline de indexação dos imóveis...")

	if reindexar:
		print("[2/4] Limpando a base vetorial antiga...")
		limpar_base_vetorial()

	print("[3/4] Carregando base, gerando documentos e gravando embeddings...")
	rag = ImovelRAG()
	rag.indexar()

	if validar:
		print("[4/4] Validando a busca com uma consulta rápida...")
		resultados = rag.buscar_avancado(
			consulta="imóvel para família com muitos quartos",
			limite=2,
			filtros=FiltroImovel(quartos_min=3)
		)
		print(f"Validação concluída: {len(resultados)} imóvel(is) encontrado(s).")

	print("Pipeline finalizado com sucesso.")


def main():

	parser = argparse.ArgumentParser(
		description="Indexa a base de imóveis no Chroma e valida o pipeline RAG."
	)
	parser.add_argument(
		"--reindexar",
		action="store_true",
		help="Remove a base vetorial atual antes de indexar novamente."
	)
	parser.add_argument(
		"--sem-validacao",
		action="store_true",
		help="Executa somente a indexação, sem validação final da busca."
	)
	args = parser.parse_args()

	print("Na primeira execução, o modelo de embeddings pode demorar um pouco para baixar.")

	executar_pipeline(
		reindexar=args.reindexar,
		validar=not args.sem_validacao,
	)

if __name__ == "__main__":

	try:
		main()
	except Exception as error:

		print(f"Falha ao indexar os imóveis: {error}")
		raise