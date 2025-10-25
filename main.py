"""
Sistema Principal de Geolocalização
Orquestra todos os agentes para encontrar o endereço do imóvel
"""

import logging
import json
from pathlib import Path
from typing import Dict, Optional
import pandas as pd
import folium

from config import (
    OUTPUT_DIR, DATA_DIR, SEARCH_CONFIG, ML_CONFIG,
    LOGGING_CONFIG
)

from agents.vision_agent import VisionAgent
from agents.search_agent import SearchAgent
from agents.matching_agent import MatchingAgent
from agents.validation_agent import ValidationAgent


# Configurar logging
logging.basicConfig(
    level=LOGGING_CONFIG["level"],
    format=LOGGING_CONFIG["format"],
    handlers=[
        logging.FileHandler(LOGGING_CONFIG["file"]),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class GeoLocalizador:
    """
    Sistema completo de geolocalização de imóveis.
    
    Pipeline:
    1. Análise visual da foto (VisionAgent)
    2. Busca geográfica (SearchAgent)
    3. Matching visual (MatchingAgent)
    4. Validação LLM (ValidationAgent)
    5. Extração de endereço
    """
    
    def __init__(self):
        logger.info("=" * 60)
        logger.info("Inicializando GeoLocalizador")
        logger.info("=" * 60)
        
        self.vision_agent = VisionAgent()
        self.search_agent = SearchAgent()
        self.matching_agent = MatchingAgent()
        self.validation_agent = ValidationAgent()
        
        # Diretórios de saída
        self.sv_dir = OUTPUT_DIR / "street_views"
        self.sv_dir.mkdir(exist_ok=True, parents=True)
        
        logger.info("✅ Todos os agentes inicializados")
    
    def localizar_imovel(
        self,
        foto_path: str | Path,
        cidade: str = None,
        bairro: str = None,
        center_lat: float = None,
        center_lon: float = None,
        radius_m: int = None
    ) -> Dict:
        """
        Localiza o imóvel e retorna endereço completo.
        
        Args:
            foto_path: Caminho da foto do imóvel
            cidade: Cidade (ex: "São Paulo")
            bairro: Bairro (ex: "Alto da Boa Vista")
            center_lat/lon: Coordenadas iniciais (opcional)
            radius_m: Raio de busca (opcional)
            
        Returns:
            Dict com endereço, coordenadas, confiança, etc.
        """
        foto_path = Path(foto_path)
        
        if not foto_path.exists():
            raise FileNotFoundError(f"Foto não encontrada: {foto_path}")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"LOCALIZANDO IMÓVEL: {foto_path.name}")
        logger.info(f"{'='*60}\n")
        
        # === ETAPA 1: Análise Visual ===
        logger.info("🔍 ETAPA 1: Análise Visual")
        query_analysis = self.vision_agent.analyze_image(foto_path)
        
        if not query_analysis["success"]:
            return {
                "success": False,
                "error": "Falha na análise visual",
                "details": query_analysis
            }
        
        # Salvar análise
        with open(OUTPUT_DIR / "analise_visual.json", "w", encoding="utf-8") as f:
            json.dump(query_analysis, f, indent=2, ensure_ascii=False)
        
        logger.info("✅ Análise visual completa")
        
        # Extrair dicas textuais
        text_hints = self.vision_agent.extract_text_hints(query_analysis)
        
        # === ETAPA 2: Busca Geográfica ===
        logger.info("\n🗺️  ETAPA 2: Busca Geográfica")
        
        # Usar coordenadas fornecidas ou padrão
        if center_lat is None or center_lon is None:
            center_lat = SEARCH_CONFIG.get("initial_lat", -23.6505)
            center_lon = SEARCH_CONFIG.get("initial_lon", -46.6815)
            logger.warning(f"Usando coordenadas padrão: ({center_lat}, {center_lon})")
        
        cidade = cidade or SEARCH_CONFIG["default_city"]
        
        candidates = self.search_agent.search_area(
            center_lat=center_lat,
            center_lon=center_lon,
            radius_m=radius_m,
            city=cidade,
            neighborhood=bairro,
            text_hints=text_hints
        )
        
        if not candidates:
            return {
                "success": False,
                "error": "Nenhum candidato encontrado na área",
                "hint": "Tente aumentar o raio de busca ou verificar cidade/bairro"
            }
        
        logger.info(f"✅ {len(candidates)} candidatos encontrados")
        
        # === ETAPA 3: Download Street Views ===
        logger.info("\n📸 ETAPA 3: Download Street Views")
        
        sv_metadata = self.search_agent.download_street_views(
            candidates,
            self.sv_dir
        )
        
        sv_metadata.to_csv(OUTPUT_DIR / "sv_metadata.csv", index=False)
        logger.info(f"✅ {len(sv_metadata)} imagens Street View")
        
        # === ETAPA 4: Matching Visual ===
        logger.info("\n🎯 ETAPA 4: Matching Visual (CLIP + SIFT)")
        
        top_matches = self.matching_agent.rank_candidates(
            foto_path,
            sv_metadata,
            self.sv_dir
        )
        
        top_matches.to_csv(OUTPUT_DIR / "candidatos.csv", index=False)
        logger.info(f"✅ {len(top_matches)} candidatos ranqueados")
        
        if len(top_matches) == 0:
            return {
                "success": False,
                "error": "Nenhum candidato passou no threshold visual",
                "hint": "Tente reduzir clip_threshold em config.py"
            }
        
        # === ETAPA 5: Validação LLM ===
        logger.info("\n🤖 ETAPA 5: Validação com Claude")
        
        # Validar top K candidatos
        top_k = min(5, len(top_matches))
        validated = self.validation_agent.validate_candidates(
            query_analysis,
            top_matches.head(top_k),
            self.sv_dir
        )
        
        validated.to_csv(OUTPUT_DIR / "candidatos_validados.csv", index=False)
        
        # === ETAPA 6: Seleção Final ===
        logger.info("\n🏆 ETAPA 6: Seleção do Melhor Match")
        
        best_match = validated.iloc[0]
        
        if best_match["final_confidence"] < ML_CONFIG["min_confidence"]:
            logger.warning(f"⚠️  Confiança baixa: {best_match['final_confidence']:.3f}")
            return {
                "success": False,
                "error": "Confiança abaixo do threshold",
                "best_match": best_match.to_dict(),
                "hint": "Resultados incertos. Tente foto de outro ângulo."
            }
        
        logger.info(f"✅ Match encontrado! Confiança: {best_match['final_confidence']:.3f}")
        
        # === ETAPA 7: Extração de Endereço ===
        logger.info("\n📍 ETAPA 7: Extração de Endereço")
        
        address = self.validation_agent.extract_address(
            best_match.to_dict(),
            query_analysis["analysis"]
        )
        
        # === Resultado Final ===
        resultado = {
            "success": True,
            "endereco": address.get("full_address", ""),
            "rua": address.get("street", ""),
            "numero": address.get("number", ""),
            "bairro": address.get("neighborhood", ""),
            "cidade": address.get("city", cidade),
            "estado": address.get("state", ""),
            "cep": address.get("zip_code", ""),
            "coordenadas": address.get("coordinates"),
            "confianca": best_match["final_confidence"],
            "scores": {
                "clip": best_match["clip_score"],
                "geometria": best_match["geom_score"],
                "llm": best_match["llm_confidence"]
            },
            "street_view_link": self._generate_sv_link(
                best_match["lat"],
                best_match["lon"],
                best_match["heading"]
            ),
            "reasoning": best_match["llm_reasoning"]
        }
        
        # Salvar resultado
        with open(OUTPUT_DIR / "resultado_final.json", "w", encoding="utf-8") as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False)
        
        # Gerar mapa
        self._generate_map(validated, query_analysis)
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 GEOLOCALIZAÇÃO CONCLUÍDA!")
        logger.info("=" * 60)
        logger.info(f"📍 Endereço: {resultado['endereco']}")
        logger.info(f"🎯 Confiança: {resultado['confianca']:.1%}")
        logger.info(f"🗺️  Mapa: {OUTPUT_DIR / 'mapa.html'}")
        logger.info("=" * 60 + "\n")
        
        return resultado
    
    def _generate_sv_link(self, lat: float, lon: float, heading: int) -> str:
        """Gera link do Google Maps Street View"""
        return (
            f"https://www.google.com/maps/@?api=1&map_action=pano"
            f"&viewpoint={lat},{lon}&heading={heading}&source=maps_sv"
        )
    
    def _generate_map(self, validated: pd.DataFrame, query_analysis: Dict):
        """Gera mapa interativo com Folium"""
        logger.info("🗺️  Gerando mapa interativo...")
        
        # Centro no melhor match
        best = validated.iloc[0]
        m = folium.Map(
            location=[best["lat"], best["lon"]],
            zoom_start=17,
            tiles="OpenStreetMap"
        )
        
        # Adicionar candidatos
        for _, row in validated.iterrows():
            conf = row["final_confidence"]
            
            # Cor baseada na confiança
            if conf >= 0.85:
                color = "red"
                icon = "star"
            elif conf >= 0.70:
                color = "orange"
                icon = "info-sign"
            else:
                color = "blue"
                icon = "question-sign"
            
            # Popup com informações
            popup_html = f"""
            <b>Confiança:</b> {conf:.1%}<br>
            <b>CLIP:</b> {row['clip_score']:.3f}<br>
            <b>Geometria:</b> {row['geom_score']:.3f}<br>
            <b>LLM:</b> {row['llm_confidence']:.3f}<br>
            <b>Match:</b> {'✅ Sim' if row['llm_is_match'] else '❌ Não'}<br>
            <b>Heading:</b> {row['heading']}°<br>
            <hr>
            <b>Raciocínio:</b><br>{row['llm_reasoning']}<br>
            <hr>
            <a href="{self._generate_sv_link(row['lat'], row['lon'], row['heading'])}" target="_blank">
                🗺️ Abrir Street View
            </a>
            """
            
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=folium.Popup(popup_html, max_width=400),
                icon=folium.Icon(color=color, icon=icon)
            ).add_to(m)
        
        # Salvar
        map_path = OUTPUT_DIR / "mapa.html"
        m.save(map_path)
        logger.info(f"✅ Mapa salvo em {map_path}")


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Geolocalização de Imóveis")
    parser.add_argument("--foto", required=True, help="Caminho da foto")
    parser.add_argument("--cidade", default="São Paulo", help="Cidade")
    parser.add_argument("--bairro", help="Bairro (opcional)")
    parser.add_argument("--lat", type=float, help="Latitude inicial")
    parser.add_argument("--lon", type=float, help="Longitude inicial")
    parser.add_argument("--raio", type=int, help="Raio de busca (metros)")
    
    args = parser.parse_args()
    
    # Executar
    geo = GeoLocalizador()
    
    resultado = geo.localizar_imovel(
        foto_path=args.foto,
        cidade=args.cidade,
        bairro=args.bairro,
        center_lat=args.lat,
        center_lon=args.lon,
        radius_m=args.raio
    )
    
    if resultado["success"]:
        print("\n✅ SUCESSO!")
        print(f"📍 {resultado['endereco']}")
        print(f"🎯 Confiança: {resultado['confianca']:.1%}")
        print(f"🗺️  Mapa: {OUTPUT_DIR / 'mapa.html'}")
    else:
        print(f"\n❌ FALHA: {resultado['error']}")
        if "hint" in resultado:
            print(f"💡 Dica: {resultado['hint']}")


def buscar_com_multiplas_fotos(
    fotos: list[str | Path],
    cidade: str = "São Paulo",
    estado: str = "SP",
    bairro: str = None,
    regiao: str = None
) -> Dict:
    """
    🎯 ANÁLISE COMBINADA: Busca usando MÚLTIPLAS fotos externas.
    
    Analisa todas as fotos, combina as informações e usa a melhor para matching.
    Aumenta precisão e confiança do resultado.
    
    Args:
        fotos: Lista de caminhos das fotos (2-5 fotos recomendado)
        cidade: Cidade para buscar (padrão: São Paulo)
        estado: Estado (padrão: SP)
        bairro: Bairro específico (ex: "Santo Amaro") - RECOMENDADO
        regiao: Região da cidade (ex: "Zona Sul") - opcional
        
    Returns:
        Dict com resultado da busca
        
    Exemplo:
        >>> resultado = buscar_com_multiplas_fotos(
        ...     fotos=["fachada_frontal.jpg", "fachada_lateral.jpg"],
        ...     cidade="São Paulo",
        ...     bairro="Santo Amaro"
        ... )
        >>> print(resultado["endereco"])
    """
    logger.info("\n" + "="*70)
    logger.info("🎯 ANÁLISE COMBINADA: Múltiplas fotos externas")
    logger.info(f"   Total de fotos: {len(fotos)}")
    logger.info("="*70)
    
    if len(fotos) < 1:
        return {
            "success": False,
            "error": "É necessário pelo menos 1 foto"
        }
    
    if len(fotos) > 5:
        logger.warning(f"⚠️  Muitas fotos ({len(fotos)}). Usando apenas as 5 primeiras.")
        fotos = fotos[:5]
    
    geo = GeoLocalizador()
    
    # 1. Analisar TODAS as fotos
    logger.info("\n🔍 ETAPA 1: Analisando todas as fotos...")
    analises = []
    pistas_combinadas = []
    
    for i, foto_path in enumerate(fotos, 1):
        foto_path = Path(foto_path)
        if not foto_path.exists():
            logger.warning(f"⚠️  Foto {i} não encontrada: {foto_path}")
            continue
            
        logger.info(f"\n   📸 Foto {i}/{len(fotos)}: {foto_path.name}")
        
        query_analysis = geo.vision_agent.analyze_image(foto_path)
        
        if query_analysis["success"]:
            analises.append({
                "foto": foto_path,
                "analysis": query_analysis["analysis"],
                "index": i
            })
            
            # Extrair pistas
            analysis = query_analysis["analysis"]
            if "text_detected" in analysis:
                pistas_combinadas.extend(analysis["text_detected"])
            if "nearby_landmarks" in analysis:
                pistas_combinadas.extend(analysis["nearby_landmarks"])
                
            logger.info(f"      ✅ Análise concluída")
        else:
            logger.warning(f"      ⚠️  Falha na análise")
    
    if not analises:
        return {
            "success": False,
            "error": "Nenhuma foto pôde ser analisada com sucesso"
        }
    
    logger.info(f"\n✅ {len(analises)} foto(s) analisada(s) com sucesso")
    logger.info(f"📝 Pistas combinadas encontradas: {len(set(pistas_combinadas))}")
    
    # 2. Selecionar melhor foto para matching
    logger.info("\n🎯 ETAPA 2: Selecionando melhor foto para matching...")
    
    # Critérios: mais características distintivas + melhor qualidade
    melhor_foto = None
    melhor_score = 0
    
    for item in analises:
        analysis = item["analysis"]
        score = 0
        
        # Pontuação baseada em características
        if "distinctive_features" in analysis:
            score += len(analysis["distinctive_features"]) * 2
        if "text_detected" in analysis:
            score += len(analysis["text_detected"]) * 3
        if "nearby_landmarks" in analysis:
            score += len(analysis["nearby_landmarks"]) * 2
        
        logger.info(f"   Foto {item['index']}: score = {score}")
        
        if score > melhor_score:
            melhor_score = score
            melhor_foto = item["foto"]
    
    if not melhor_foto:
        melhor_foto = analises[0]["foto"]
    
    logger.info(f"\n✅ Melhor foto selecionada: {melhor_foto.name}")
    
    # 3. Buscar usando a melhor foto
    logger.info("\n🔍 ETAPA 3: Executando busca com foto selecionada...")
    
    return buscar_apenas_por_foto(
        foto_path=melhor_foto,
        cidade=cidade,
        estado=estado,
        bairro=bairro,
        regiao=regiao
    )


def buscar_apenas_por_foto(
    foto_path: str | Path,
    cidade: str = "São Paulo",
    estado: str = "SP",
    bairro: str = None,
    regiao: str = None
) -> Dict:
    """
    🚨 MODO INVESTIGAÇÃO: Busca APENAS pela foto, sem coordenadas.
    
    Ideal para casos onde você só tem a imagem e precisa encontrar o local.
    Usa estratégia de busca ampla + refinamento progressivo.
    
    Args:
        foto_path: Caminho da foto
        cidade: Cidade para buscar (padrão: São Paulo)
        estado: Estado (padrão: SP)
        bairro: Bairro específico (ex: "Santo Amaro") - RECOMENDADO
        regiao: Região da cidade (ex: "Zona Sul") - opcional
        
    Returns:
        Dict com resultado da busca
        
    Exemplo:
        >>> resultado = buscar_apenas_por_foto(
        ...     "casa_desconhecida.jpg",
        ...     cidade="São Paulo",
        ...     bairro="Santo Amaro"
        ... )
        >>> print(resultado["endereco"])
    """
    logger.info("\n" + "="*70)
    logger.info("🚨 MODO INVESTIGAÇÃO: Busca apenas por foto")
    logger.info("="*70)
    
    geo = GeoLocalizador()
    
    # 1. Análise visual para extrair pistas
    logger.info("\n🔍 Analisando foto para extrair pistas...")
    query_analysis = geo.vision_agent.analyze_image(foto_path)
    
    if not query_analysis["success"]:
        return {
            "success": False,
            "error": "Falha na análise da imagem",
            "details": query_analysis
        }
    
    analysis = query_analysis["analysis"]
    
    # 2. Extrair pistas da análise
    pistas = []
    
    # Texto detectado (placas, números, nomes de rua)
    if "text_detected" in analysis:
        pistas.extend(analysis["text_detected"])
        logger.info(f"📝 Texto detectado: {analysis['text_detected']}")
    
    # Pontos de referência mencionados
    if "nearby_landmarks" in analysis:
        pistas.extend(analysis["nearby_landmarks"])
        logger.info(f"🏛️  Pontos de referência: {analysis['nearby_landmarks']}")
    
    # Características únicas
    if "distinctive_features" in analysis:
        logger.info(f"✨ Características: {analysis['distinctive_features']}")
    
    # 3. Estratégia de busca progressiva
    # Construir endereço para geocodificação com fallback
    import requests
    from config import GOOGLE_KEY
    
    geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
    center_lat = None
    center_lon = None
    local_usado = None
    
    # Tentar múltiplas combinações
    tentativas = []
    
    if bairro:
        tentativas = [
            f"{bairro}, {cidade}, {estado}",
            f"{bairro}, {cidade}",
            f"{bairro}, São Paulo, SP",
            f"{cidade}, {estado}"  # Fallback para cidade
        ]
        logger.info(f"\n🎯 Tentando localizar: {bairro}, {cidade}, {estado}")
    elif regiao:
        tentativas = [
            f"{regiao}, {cidade}, {estado}",
            f"{regiao}, {cidade}",
            f"{cidade}, {estado}"
        ]
        logger.info(f"\n🎯 Tentando localizar: {regiao}, {cidade}, {estado}")
    else:
        tentativas = [
            f"{cidade}, {estado}",
            f"{cidade}, São Paulo"
        ]
        logger.info(f"\n🎯 Tentando localizar: {cidade}, {estado}")
    
    logger.info("   Estratégia: Busca ampla → Refinamento progressivo")
    
    # Tentar geocodificar com fallback
    for tentativa in tentativas:
        logger.info(f"   Tentando: {tentativa}")
        
        params = {
            "address": tentativa,
            "key": GOOGLE_KEY,
            "region": "br"  # Priorizar Brasil
        }
        
        response = requests.get(geocode_url, params=params)
        geocode_data = response.json()
        
        if geocode_data["status"] == "OK":
            location = geocode_data["results"][0]["geometry"]["location"]
            center_lat = location["lat"]
            center_lon = location["lng"]
            local_usado = tentativa
            logger.info(f"   ✅ Geocodificado com sucesso!")
            break
        else:
            logger.info(f"   ❌ Falhou: {geocode_data.get('status')}")
    
    if center_lat is None or center_lon is None:
        return {
            "success": False,
            "error": f"Não foi possível geocodificar nenhuma das tentativas",
            "tentativas": tentativas,
            "hint": "Tente especificar coordenadas manualmente ou use um bairro mais conhecido"
        }
    
    logger.info(f"\n📍 Centro da área: ({center_lat}, {center_lon})")
    logger.info(f"   Local usado: {local_usado}")
    
    # 4. Busca em múltiplos raios (progressivo)
    # Ajustar raios baseado na especificidade
    if bairro:
        raios = [2000, 3000, 5000]  # Bairro específico: raios menores
        logger.info("   Raios de busca: 2km, 3km, 5km (bairro específico)")
    elif regiao:
        raios = [3000, 5000, 8000]  # Região: raios médios
        logger.info("   Raios de busca: 3km, 5km, 8km (região)")
    else:
        raios = [5000, 10000, 20000]  # Cidade inteira: raios grandes
        logger.info("   Raios de busca: 5km, 10km, 20km (cidade)")
    
    melhor_resultado = None
    melhor_confianca = 0
    
    for radius_m in raios:
        logger.info(f"\n🔄 Tentativa com raio de {radius_m}m...")
        
        try:
            resultado = geo.localizar_imovel(
                foto_path=foto_path,
                cidade=cidade,
                center_lat=center_lat,
                center_lon=center_lon,
                radius_m=radius_m
            )
            
            if resultado["success"]:
                confianca = resultado["confianca"]
                logger.info(f"✅ Encontrado! Confiança: {confianca:.1%}")
                
                if confianca > melhor_confianca:
                    melhor_resultado = resultado
                    melhor_confianca = confianca
                
                # Se confiança alta, parar
                if confianca >= 0.85:
                    logger.info("🎉 Alta confiança! Parando busca.")
                    break
            else:
                logger.info(f"⚠️  Não encontrado neste raio")
                
        except Exception as e:
            logger.error(f"❌ Erro na busca: {e}")
            continue
    
    if melhor_resultado:
        logger.info("\n" + "="*70)
        logger.info("🎉 LOCALIZAÇÃO ENCONTRADA!")
        logger.info("="*70)
        return melhor_resultado
    else:
        return {
            "success": False,
            "error": "Não foi possível localizar o imóvel",
            "hint": "Tente: 1) Foto de melhor qualidade, 2) Especificar bairro, 3) Verificar se há Street View na região",
            "pistas_encontradas": pistas
        }
