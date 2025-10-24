"""
Agente 3: Matching Visual (CLIP + SIFT/RANSAC)
Compara foto do usuário com Street Views usando embeddings + geometria
"""

import logging
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import cv2
import torch
import open_clip
from PIL import Image
from tqdm import tqdm
import pandas as pd

from config import ML_CONFIG

logger = logging.getLogger(__name__)


class MatchingAgent:
    """
    Agente responsável por comparação visual multimodal:
    1. CLIP (ViT-bigG) - similaridade semântica (cores, arquitetura)
    2. SIFT + RANSAC - matching geométrico (pontos de interesse)
    3. Score combinado ponderado
    """
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Usando device: {self.device}")
        
        # Carregar modelo CLIP
        logger.info(f"Carregando {ML_CONFIG['clip_model']}...")
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            ML_CONFIG["clip_model"],
            pretrained=ML_CONFIG["clip_pretrained"],
            device=self.device
        )
        self.model.eval()
        
        # Cache de embeddings
        self.embedding_cache = {}
        
        logger.info("MatchingAgent inicializado")
    
    def compare_images(
        self,
        query_path: str | Path,
        database_paths: List[str | Path],
        compute_geometry: bool = True
    ) -> pd.DataFrame:
        """
        Compara imagem de consulta com banco de imagens.
        
        Returns:
            DataFrame com [db_path, clip_score, geom_score, combined_score]
        """
        query_path = Path(query_path)
        
        logger.info(f"Comparando {query_path.name} com {len(database_paths)} candidatos")
        
        # Embedding da query
        query_emb = self._get_embedding(query_path)
        
        results = []
        
        for db_path in tqdm(database_paths, desc="Comparando imagens"):
            db_path = Path(db_path)
            
            # CLIP score
            db_emb = self._get_embedding(db_path)
            clip_score = float(np.dot(query_emb, db_emb))
            
            # Geometria (só se CLIP passar threshold)
            geom_score = 0.0
            if compute_geometry and clip_score >= ML_CONFIG["clip_threshold"]:
                geom_score = self._geometric_match(query_path, db_path)
            
            # Score combinado
            combined_score = (
                ML_CONFIG["clip_weight"] * clip_score +
                ML_CONFIG["geom_weight"] * geom_score
            )
            
            results.append({
                "db_path": str(db_path),
                "db_filename": db_path.name,
                "clip_score": clip_score,
                "geom_score": geom_score,
                "combined_score": combined_score
            })
        
        df = pd.DataFrame(results)
        df = df.sort_values("combined_score", ascending=False).reset_index(drop=True)
        
        logger.info(f"Top match: {df.iloc[0]['db_filename']} (score: {df.iloc[0]['combined_score']:.3f})")
        
        return df
    
    def rank_candidates(
        self,
        query_path: str | Path,
        sv_metadata: pd.DataFrame,
        sv_dir: Path,
        top_k: int = None
    ) -> pd.DataFrame:
        """
        Ranqueia candidatos do Street View.
        
        Args:
            query_path: Foto do usuário
            sv_metadata: DataFrame com metadados dos SVs (filename, lat, lon, etc)
            sv_dir: Diretório com imagens SV
            top_k: Retornar apenas top K
            
        Returns:
            DataFrame com candidatos ranqueados + scores
        """
        top_k = top_k or ML_CONFIG["top_k_candidates"]
        
        # Caminhos das imagens SV
        sv_paths = [sv_dir / fn for fn in sv_metadata["filename"]]
        
        # Comparar
        scores_df = self.compare_images(query_path, sv_paths)
        
        # Merge com metadados
        scores_df["filename"] = scores_df["db_filename"]
        merged = scores_df.merge(sv_metadata, on="filename", how="left")
        
        # Filtrar por threshold
        merged = merged[merged["clip_score"] >= ML_CONFIG["clip_threshold"]]
        
        # Top K
        merged = merged.head(top_k)
        
        logger.info(f"Candidatos acima de threshold: {len(merged)}")
        
        return merged
    
    def _get_embedding(self, image_path: Path) -> np.ndarray:
        """
        Obtém embedding CLIP (com cache).
        """
        cache_key = str(image_path)
        
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]
        
        # Carregar e preprocessar
        img = Image.open(image_path).convert("RGB")
        img_tensor = self.preprocess(img).unsqueeze(0).to(self.device)
        
        # Inferência
        with torch.no_grad(), torch.cuda.amp.autocast(enabled=(self.device == 'cuda')):
            embedding = self.model.encode_image(img_tensor)
            embedding = embedding / embedding.norm(dim=-1, keepdim=True)
        
        emb_np = embedding.squeeze(0).detach().cpu().numpy()
        
        # Cachear
        self.embedding_cache[cache_key] = emb_np
        
        return emb_np
    
    def _geometric_match(self, img1_path: Path, img2_path: Path) -> float:
        """
        Matching geométrico com SIFT + RANSAC.
        
        Returns:
            Score normalizado [0, 1]
        """
        # Carregar imagens em grayscale
        img1 = cv2.imread(str(img1_path))
        img2 = cv2.imread(str(img2_path))
        
        if img1 is None or img2 is None:
            return 0.0
        
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        
        # Detectar features com SIFT
        sift = cv2.SIFT_create(nfeatures=ML_CONFIG["sift_features"])
        
        kp1, desc1 = sift.detectAndCompute(gray1, None)
        kp2, desc2 = sift.detectAndCompute(gray2, None)
        
        if desc1 is None or desc2 is None:
            return 0.0
        
        # Matching com FLANN
        index_params = dict(algorithm=1, trees=5)  # FLANN_INDEX_KDTREE
        search_params = dict(checks=50)
        
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        matches = flann.knnMatch(desc1, desc2, k=2)
        
        # Ratio test (Lowe's)
        good_matches = []
        for m, n in matches:
            if m.distance < ML_CONFIG["sift_match_ratio"] * n.distance:
                good_matches.append(m)
        
        if len(good_matches) < ML_CONFIG["min_inliers"]:
            return 0.0
        
        # RANSAC para filtrar outliers
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        
        H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        
        if mask is None:
            return 0.0
        
        inliers = int(mask.sum())
        
        # Normalizar (60 inliers = score 1.0)
        score = min(1.0, inliers / 60.0)
        
        return score
    
    def visualize_match(
        self,
        img1_path: Path,
        img2_path: Path,
        output_path: Path
    ):
        """
        Gera visualização do matching com linhas conectando features.
        """
        img1 = cv2.imread(str(img1_path))
        img2 = cv2.imread(str(img2_path))
        
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        
        sift = cv2.SIFT_create(nfeatures=ML_CONFIG["sift_features"])
        
        kp1, desc1 = sift.detectAndCompute(gray1, None)
        kp2, desc2 = sift.detectAndCompute(gray2, None)
        
        if desc1 is None or desc2 is None:
            logger.warning("Sem features detectadas para visualização")
            return
        
        # Matching
        bf = cv2.BFMatcher()
        matches = bf.knnMatch(desc1, desc2, k=2)
        
        good = []
        for m, n in matches:
            if m.distance < 0.75 * n.distance:
                good.append([m])
        
        # Desenhar
        img_matches = cv2.drawMatchesKnn(
            img1, kp1, img2, kp2, good, None,
            flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
        )
        
        cv2.imwrite(str(output_path), img_matches)
        logger.info(f"Visualização salva em {output_path}")


if __name__ == "__main__":
    # Teste do agente
    import sys
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 3:
        print("Uso: python matching_agent.py <query_img> <db_img>")
        sys.exit(1)
    
    agent = MatchingAgent()
    
    query = Path(sys.argv[1])
    db = Path(sys.argv[2])
    
    # Comparar
    df = agent.compare_images(query, [db])
    print("\n✅ Resultado:")
    print(df)
    
    # Visualizar
    output = Path("match_visualization.jpg")
    agent.visualize_match(query, db, output)
    print(f"\n📊 Visualização salva em {output}")
