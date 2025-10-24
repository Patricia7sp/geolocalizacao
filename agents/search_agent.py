"""
Agente 2: Busca Geográfica Inteligente
Implementa estratégia de funil (macro → micro) para encontrar candidatos
"""

import logging
import time
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import requests
from urllib.parse import urlencode
import pandas as pd
import numpy as np
from tqdm import tqdm

from config import GOOGLE_API_KEY, SEARCH_CONFIG, CACHE_DIR

logger = logging.getLogger(__name__)


class SearchAgent:
    """
    Agente responsável por buscar candidatos geográficos usando:
    1. Google Places API (busca de condomínios)
    2. Grid Search (pontos espaçados)
    3. Street View Metadata (verificar disponibilidade)
    4. Refinamento progressivo (focar em áreas promissoras)
    """
    
    def __init__(self):
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY não configurada")
        
        self.api_key = GOOGLE_API_KEY
        self.cache_dir = CACHE_DIR / "search"
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        
        logger.info("SearchAgent inicializado")
    
    def search_area(
        self,
        center_lat: float,
        center_lon: float,
        radius_m: int = None,
        city: str = None,
        neighborhood: str = None,
        text_hints: Dict = None
    ) -> List[Dict]:
        """
        Busca candidatos na área especificada.
        
        Strategy:
        1. Se houver dicas textuais (nome do condomínio, rua) → busca direta
        2. Caso contrário → busca de condomínios + grid search
        
        Returns:
            Lista de coordenadas candidatas com metadados
        """
        radius_m = radius_m or SEARCH_CONFIG["initial_radius_m"]
        
        candidates = []
        
        # Passo 1: Buscar condomínios via Places API
        logger.info(f"Buscando condomínios em raio de {radius_m}m")
        condos = self._search_condos(center_lat, center_lon, radius_m, city, neighborhood)
        logger.info(f"Encontrados {len(condos)} condomínios")
        
        # Adicionar condomínios aos candidatos
        for condo in condos:
            candidates.append({
                "lat": condo["lat"],
                "lon": condo["lon"],
                "source": "places_api",
                "name": condo["name"],
                "address": condo.get("address", ""),
                "type": "condominium"
            })
        
        # Passo 2: Grid Search (pontos espaçados)
        logger.info("Gerando grid de busca...")
        grid_points = self._generate_grid(
            center_lat, center_lon, radius_m, 
            spacing=SEARCH_CONFIG["grid_spacing_m"]
        )
        logger.info(f"Grid com {len(grid_points)} pontos")
        
        for lat, lon in grid_points:
            candidates.append({
                "lat": lat,
                "lon": lon,
                "source": "grid_search",
                "type": "grid_point"
            })
        
        # Passo 3: Verificar disponibilidade de Street View
        logger.info("Verificando Street View disponível...")
        candidates_with_sv = self._filter_by_street_view(candidates)
        
        logger.info(f"Total de candidatos com Street View: {len(candidates_with_sv)}")
        
        return candidates_with_sv
    
    def refine_search(self, candidate_coords: Tuple[float, float]) -> List[Dict]:
        """
        Refinamento: cria grid denso ao redor de um candidato promissor.
        """
        lat, lon = candidate_coords
        radius = SEARCH_CONFIG["refinement_radius_m"]
        spacing = SEARCH_CONFIG["refinement_spacing_m"]
        
        logger.info(f"Refinando busca ao redor de ({lat:.6f}, {lon:.6f})")
        
        grid = self._generate_grid(lat, lon, radius, spacing)
        
        candidates = []
        for glat, glon in grid:
            candidates.append({
                "lat": glat,
                "lon": glon,
                "source": "refinement",
                "type": "refined_point"
            })
        
        # Filtrar por Street View
        refined = self._filter_by_street_view(candidates)
        logger.info(f"Refinamento gerou {len(refined)} pontos com SV")
        
        return refined
    
    def _search_condos(
        self, 
        lat: float, 
        lon: float, 
        radius_m: int,
        city: str = None,
        neighborhood: str = None
    ) -> List[Dict]:
        """
        Busca condomínios usando Google Places API (New).
        """
        queries = [
            "condomínio residencial",
            "condomínio fechado",
        ]
        
        if neighborhood:
            queries.append(f"condomínio {neighborhood}")
        if city:
            queries.append(f"condomínio {city}")
        
        all_results = []
        
        for query in queries:
            results = self._places_text_search(query, lat, lon, radius_m)
            all_results.extend(results)
            time.sleep(SEARCH_CONFIG["request_delay"])
        
        # Remover duplicatas por nome e coordenadas
        df = pd.DataFrame(all_results)
        if len(df) > 0:
            df = df.drop_duplicates(subset=["name", "lat", "lon"]).reset_index(drop=True)
            return df.to_dict('records')
        
        return []
    
    def _places_text_search(
        self, 
        query: str, 
        lat: float, 
        lon: float, 
        radius_m: int
    ) -> List[Dict]:
        """
        Places API (New) - Text Search
        """
        url = "https://places.googleapis.com/v1/places:searchText"
        
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "places.displayName,places.location,places.id,places.formattedAddress"
        }
        
        body = {
            "textQuery": query,
            "locationBias": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lon},
                    "radius": radius_m
                }
            },
            "maxResultCount": 20
        }
        
        results = []
        page_token = None
        
        for _ in range(3):  # max 3 páginas
            if page_token:
                body["pageToken"] = page_token
            
            try:
                r = requests.post(url, headers=headers, json=body, timeout=30)
                r.raise_for_status()
                data = r.json()
                
                for place in data.get("places", []):
                    results.append({
                        "name": place["displayName"]["text"],
                        "lat": place["location"]["latitude"],
                        "lon": place["location"]["longitude"],
                        "address": place.get("formattedAddress", "")
                    })
                
                page_token = data.get("nextPageToken")
                if not page_token:
                    break
                    
            except requests.RequestException as e:
                logger.error(f"Erro ao buscar Places: {e}")
                break
        
        return results
    
    def _generate_grid(
        self, 
        center_lat: float, 
        center_lon: float, 
        radius_m: int, 
        spacing: int
    ) -> List[Tuple[float, float]]:
        """
        Gera grid de pontos espaçados uniformemente.
        
        spacing: espaçamento em metros
        """
        # Conversão aproximada: 1 grau = ~111km
        deg_per_m_lat = 1 / 111000
        deg_per_m_lon = 1 / (111000 * np.cos(np.radians(center_lat)))
        
        radius_deg_lat = radius_m * deg_per_m_lat
        radius_deg_lon = radius_m * deg_per_m_lon
        
        spacing_deg_lat = spacing * deg_per_m_lat
        spacing_deg_lon = spacing * deg_per_m_lon
        
        lats = np.arange(
            center_lat - radius_deg_lat,
            center_lat + radius_deg_lat,
            spacing_deg_lat
        )
        lons = np.arange(
            center_lon - radius_deg_lon,
            center_lon + radius_deg_lon,
            spacing_deg_lon
        )
        
        points = []
        for lat in lats:
            for lon in lons:
                # Verificar se está dentro do círculo
                dist = self._haversine_distance(center_lat, center_lon, lat, lon)
                if dist <= radius_m:
                    points.append((lat, lon))
        
        return points
    
    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        """
        Calcula distância entre dois pontos em metros.
        """
        R = 6371000  # raio da Terra em metros
        
        phi1 = np.radians(lat1)
        phi2 = np.radians(lat2)
        delta_phi = np.radians(lat2 - lat1)
        delta_lambda = np.radians(lon2 - lon1)
        
        a = np.sin(delta_phi/2)**2 + \
            np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c
    
    def _filter_by_street_view(self, candidates: List[Dict]) -> List[Dict]:
        """
        Verifica quais candidatos têm Street View disponível (ano >= min_year).
        """
        min_year = SEARCH_CONFIG["sv_min_year"]
        filtered = []
        
        for cand in tqdm(candidates, desc="Verificando Street View"):
            lat, lon = cand["lat"], cand["lon"]
            
            meta = self._sv_metadata(lat, lon)
            
            if meta.get("status") != "OK":
                continue
            
            # Verificar ano
            date_str = meta.get("date", "")
            if date_str:
                try:
                    year = int(date_str.split("-")[0])
                    if year < min_year:
                        continue
                except:
                    continue
            
            # Adicionar metadados do SV
            cand["sv_available"] = True
            cand["sv_date"] = date_str
            cand["sv_pano_id"] = meta.get("pano_id")
            cand["sv_lat"] = meta.get("location", {}).get("lat", lat)
            cand["sv_lon"] = meta.get("location", {}).get("lng", lon)
            
            filtered.append(cand)
            
            time.sleep(SEARCH_CONFIG["request_delay"])
        
        return filtered
    
    def _sv_metadata(self, lat: float, lon: float) -> Dict:
        """
        Street View Metadata API
        """
        url = "https://maps.googleapis.com/maps/api/streetview/metadata?" + urlencode({
            "location": f"{lat},{lon}",
            "key": self.api_key
        })
        
        try:
            r = requests.get(url, timeout=20)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            logger.error(f"Erro ao buscar SV metadata: {e}")
            return {"status": "ERROR"}
    
    def download_street_views(
        self, 
        candidates: List[Dict], 
        output_dir: Path
    ) -> pd.DataFrame:
        """
        Baixa imagens do Street View para todos os candidatos.
        
        Returns:
            DataFrame com metadados dos downloads
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True, parents=True)
        
        rows = []
        download_count = 0
        max_downloads = SEARCH_CONFIG["max_sv_downloads"]
        
        for i, cand in enumerate(tqdm(candidates, desc="Baixando Street Views")):
            if download_count >= max_downloads:
                logger.warning(f"Limite de {max_downloads} downloads atingido")
                break
            
            lat = cand.get("sv_lat", cand["lat"])
            lon = cand.get("sv_lon", cand["lon"])
            
            for heading in SEARCH_CONFIG["sv_headings"]:
                filename = f"sv_{i:04d}_h{heading}.jpg"
                filepath = output_dir / filename
                
                # Pular se já existe
                if filepath.exists():
                    rows.append({
                        "candidate_idx": i,
                        "lat": lat,
                        "lon": lon,
                        "heading": heading,
                        "filename": filename,
                        "source": cand.get("source"),
                        "name": cand.get("name", ""),
                        "address": cand.get("address", "")
                    })
                    continue
                
                # Baixar
                url = self._sv_static_url(lat, lon, heading)
                
                try:
                    r = requests.get(url, timeout=30)
                    r.raise_for_status()
                    
                    with open(filepath, "wb") as f:
                        f.write(r.content)
                    
                    rows.append({
                        "candidate_idx": i,
                        "lat": lat,
                        "lon": lon,
                        "heading": heading,
                        "filename": filename,
                        "source": cand.get("source"),
                        "name": cand.get("name", ""),
                        "address": cand.get("address", "")
                    })
                    
                    download_count += 1
                    time.sleep(SEARCH_CONFIG["request_delay"])
                    
                except requests.RequestException as e:
                    logger.error(f"Erro ao baixar {filename}: {e}")
        
        df = pd.DataFrame(rows)
        logger.info(f"Total de imagens baixadas: {download_count}")
        
        return df
    
    def _sv_static_url(self, lat: float, lon: float, heading: int) -> str:
        """
        Gera URL do Street View Static API
        """
        params = {
            "size": SEARCH_CONFIG["sv_size"],
            "location": f"{lat},{lon}",
            "heading": heading,
            "fov": SEARCH_CONFIG["sv_fov"],
            "pitch": 0,
            "key": self.api_key
        }
        return "https://maps.googleapis.com/maps/api/streetview?" + urlencode(params)


if __name__ == "__main__":
    # Teste do agente
    logging.basicConfig(level=logging.INFO)
    
    agent = SearchAgent()
    
    # Buscar na área do Alto da Boa Vista
    candidates = agent.search_area(
        center_lat=-23.6505,
        center_lon=-46.6815,
        radius_m=1000,
        city="São Paulo",
        neighborhood="Alto da Boa Vista"
    )
    
    print(f"\n✅ Encontrados {len(candidates)} candidatos com Street View")
    
    if candidates:
        # Baixar primeiras 10 imagens para teste
        from config import OUTPUT_DIR
        sv_dir = OUTPUT_DIR / "street_views_test"
        
        df = agent.download_street_views(candidates[:2], sv_dir)
        print(f"\n✅ {len(df)} imagens baixadas em {sv_dir}")
        print(df.head())
