"""
Script de teste rápido do sistema
"""

import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from main import GeoLocalizador
import logging

logging.basicConfig(level=logging.INFO)


def teste_basico():
    """Teste básico do sistema"""
    
    print("\n" + "="*60)
    print("🧪 TESTE DO SISTEMA DE GEOLOCALIZAÇÃO")
    print("="*60 + "\n")
    
    # Verificar se há foto de teste
    test_image = Path("test_image.jpg")
    
    if not test_image.exists():
        print("❌ Crie um arquivo 'test_image.jpg' para testar")
        print("   Ou use: python test_sistema.py <caminho_foto>")
        return
    
    # Inicializar sistema
    print("📦 Inicializando sistema...")
    geo = GeoLocalizador()
    
    # Executar geolocalização
    print("\n🚀 Iniciando busca...\n")
    
    resultado = geo.localizar_imovel(
        foto_path=test_image,
        cidade="São Paulo",
        bairro="Alto da Boa Vista",
        center_lat=-23.6505,
        center_lon=-46.6815,
        radius_m=2000
    )
    
    # Exibir resultado
    print("\n" + "="*60)
    
    if resultado["success"]:
        print("✅ RESULTADO ENCONTRADO!")
        print("="*60)
        print(f"\n📍 Endereço: {resultado['endereco']}")
        print(f"🏠 Rua: {resultado['rua']}")
        print(f"🔢 Número: {resultado['numero']}")
        print(f"🏘️  Bairro: {resultado['bairro']}")
        print(f"🏙️  Cidade: {resultado['cidade']}")
        print(f"📮 CEP: {resultado['cep']}")
        print(f"\n🎯 Confiança: {resultado['confianca']:.1%}")
        print(f"\n📊 Scores:")
        print(f"   - CLIP: {resultado['scores']['clip']:.3f}")
        print(f"   - Geometria: {resultado['scores']['geometria']:.3f}")
        print(f"   - LLM: {resultado['scores']['llm']:.3f}")
        print(f"\n🗺️  Street View: {resultado['street_view_link']}")
        print(f"\n💭 Raciocínio: {resultado['reasoning']}")
        
    else:
        print("❌ FALHA NA BUSCA")
        print("="*60)
        print(f"\n⚠️  Erro: {resultado['error']}")
        if 'hint' in resultado:
            print(f"💡 Dica: {resultado['hint']}")
    
    print("\n" + "="*60 + "\n")


def teste_individual():
    """Testa cada agente individualmente"""
    
    print("\n🧪 TESTE INDIVIDUAL DOS AGENTES\n")
    
    test_image = Path("test_image.jpg")
    if not test_image.exists():
        print("❌ Crie 'test_image.jpg' para testar")
        return
    
    # 1. Vision Agent
    print("\n1️⃣  Testando VisionAgent...")
    from agents.vision_agent import VisionAgent
    
    vision = VisionAgent()
    analysis = vision.analyze_image(test_image)
    
    if analysis["success"]:
        print("✅ Análise visual OK")
        print(f"   Estilo: {analysis['analysis']['architecture']['style']}")
    else:
        print(f"❌ Falha: {analysis['error']}")
        return
    
    # 2. Search Agent
    print("\n2️⃣  Testando SearchAgent...")
    from agents.search_agent import SearchAgent
    
    search = SearchAgent()
    candidates = search.search_area(
        center_lat=-23.6505,
        center_lon=-46.6815,
        radius_m=1000,
        city="São Paulo"
    )
    print(f"✅ {len(candidates)} candidatos encontrados")
    
    # 3. Matching Agent
    if candidates:
        print("\n3️⃣  Testando MatchingAgent...")
        from agents.matching_agent import MatchingAgent
        from config import OUTPUT_DIR
        
        sv_dir = OUTPUT_DIR / "test_sv"
        sv_dir.mkdir(exist_ok=True, parents=True)
        
        # Baixar algumas imagens
        sv_meta = search.download_street_views(candidates[:2], sv_dir)
        
        if len(sv_meta) > 0:
            matching = MatchingAgent()
            results = matching.compare_images(
                test_image,
                [sv_dir / fn for fn in sv_meta["filename"]]
            )
            print(f"✅ Top match score: {results.iloc[0]['combined_score']:.3f}")
        else:
            print("⚠️  Nenhum Street View baixado")
    
    print("\n✅ Teste individual completo!\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--individual":
            teste_individual()
        else:
            # Teste com foto fornecida
            test_image = Path(sys.argv[1])
            if test_image.exists():
                geo = GeoLocalizador()
                resultado = geo.localizar_imovel(test_image)
                
                if resultado["success"]:
                    print(f"\n✅ {resultado['endereco']}")
                else:
                    print(f"\n❌ {resultado['error']}")
            else:
                print(f"❌ Arquivo não encontrado: {test_image}")
    else:
        teste_basico()
