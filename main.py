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
