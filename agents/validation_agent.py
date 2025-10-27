"""
Agente 4: Validação com LLM
Valida matches usando OpenAI para análise contextual profunda
"""

import logging
import json
from typing import Dict, List
from pathlib import Path
from openai import OpenAI
import pandas as pd

from config import LLM_CONFIG, PROMPTS, OPENAI_API_KEY, ML_CONFIG

logger = logging.getLogger(__name__)


class ValidationAgent:
    """
    Agente responsável pela validação final dos candidatos:
    1. Comparação contextual detalhada (OpenAI)
    2. Verificação de discrepâncias
    3. Score de confiança final
    """
    
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY não configurada")
        
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = LLM_CONFIG["validation_model"]
        
        logger.info("ValidationAgent inicializado")
    
    def validate_candidates(
        self,
        query_analysis: Dict,
        candidates_df: pd.DataFrame,
        sv_dir: Path
    ) -> pd.DataFrame:
        """
        Valida top candidatos usando Claude.
        
        Args:
            query_analysis: Análise visual da foto do usuário
            candidates_df: DataFrame com candidatos (filename, lat, lon, scores)
            sv_dir: Diretório com imagens Street View
            
        Returns:
            DataFrame com validação LLM adicionada
        """
        logger.info(f"Validando {len(candidates_df)} candidatos com LLM")
        
        results = []
        
        for _, row in candidates_df.iterrows():
            sv_path = sv_dir / row["filename"]
            
            # Analisar imagem SV
            from agents.vision_agent import VisionAgent
            vision_agent = VisionAgent()
            sv_analysis = vision_agent.analyze_image(sv_path)
            
            if not sv_analysis.get("success"):
                logger.warning(f"Falha ao analisar {sv_path.name}")
                continue
            
            # Validar match
            validation = self._validate_match(
                query_analysis["analysis"],
                sv_analysis["analysis"],
                row["lat"],
                row["lon"],
                row["combined_score"]
            )
            
            # Adicionar ao resultado
            result_row = row.to_dict()
            result_row.update({
                "llm_is_match": validation["is_match"],
                "llm_confidence": validation["confidence"],
                "llm_reasoning": validation["reasoning"],
                "matching_elements": ", ".join(validation.get("matching_elements", [])),
                "discrepancies": ", ".join(validation.get("discrepancies", [])),
                
                # Score final combinado
                "final_confidence": self._compute_final_confidence(
                    row["combined_score"],
                    validation["confidence"],
                    validation["is_match"]
                )
            })
            
            results.append(result_row)
        
        df = pd.DataFrame(results)
        df = df.sort_values("final_confidence", ascending=False).reset_index(drop=True)
        
        logger.info(f"Validação completa. Top match confidence: {df.iloc[0]['final_confidence']:.3f}")
        
        return df
    
    def _validate_match(
        self,
        query_desc: Dict,
        sv_desc: Dict,
        lat: float,
        lon: float,
        visual_score: float
    ) -> Dict:
        """
        Valida se duas descrições correspondem ao mesmo imóvel.
        """
        prompt = PROMPTS["match_validation"].format(
            desc_user=json.dumps(query_desc, indent=2, ensure_ascii=False),
            desc_sv=json.dumps(sv_desc, indent=2, ensure_ascii=False),
            lat=lat,
            lon=lon,
            visual_score=visual_score
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=LLM_CONFIG["max_tokens"],
                temperature=LLM_CONFIG["temperature"],
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            validation = json.loads(response_text.strip())
            
            # Validar estrutura do JSON
            if "is_match" not in validation:
                logger.warning(f"JSON sem 'is_match': {validation}")
                validation["is_match"] = False
            if "confidence" not in validation:
                validation["confidence"] = 0.0
            if "reasoning" not in validation:
                validation["reasoning"] = "Resposta incompleta do LLM"
            if "matching_elements" not in validation:
                validation["matching_elements"] = []
            if "discrepancies" not in validation:
                validation["discrepancies"] = []
            
            return validation
            
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao parsear JSON: {e}")
            logger.error(f"Resposta: {response_text}")
            return {
                "is_match": False,
                "confidence": 0.0,
                "reasoning": "Erro no parsing da resposta",
                "matching_elements": [],
                "discrepancies": []
            }
            
        except Exception as e:
            logger.error(f"Erro na API: {e}")
            return {
                "is_match": False,
                "confidence": 0.0,
                "reasoning": f"API Error: {e}",
                "matching_elements": [],
                "discrepancies": []
            }
    
    def _compute_final_confidence(
        self,
        visual_score: float,
        llm_confidence: float,
        is_match: bool
    ) -> float:
        """
        Combina scores visual e LLM para confiança final.
        
        Se LLM diz que não é match, reduz drasticamente a confiança.
        """
        if not is_match:
            return min(visual_score, llm_confidence) * 0.5
        
        # Combinar com pesos
        context_weight = ML_CONFIG["context_weight"] / (ML_CONFIG["clip_weight"] + ML_CONFIG["geom_weight"])
        
        final = (
            visual_score * (1 - context_weight) +
            llm_confidence * context_weight
        )
        
        return final
    
    def extract_address(
        self,
        best_match: Dict,
        query_analysis: Dict
    ) -> Dict:
        """
        Extrai endereço completo do melhor match.
        """
        lat = best_match["lat"]
        lon = best_match["lon"]
        
        # Contexto geográfico
        geo_context = {
            "source": best_match.get("source"),
            "name": best_match.get("name", ""),
            "address": best_match.get("address", "")
        }
        
        prompt = PROMPTS["address_extraction"].format(
            lat=lat,
            lon=lon,
            visual_analysis=json.dumps(query_analysis, indent=2, ensure_ascii=False),
            geo_context=json.dumps(geo_context, indent=2, ensure_ascii=False),
            nearby_places=best_match.get("name", "N/A")
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=LLM_CONFIG["max_tokens"],
                temperature=LLM_CONFIG["temperature"],
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            address = json.loads(response_text.strip())
            
            # Adicionar coordenadas
            address["coordinates"] = {"lat": lat, "lon": lon}
            
            return address
            
        except Exception as e:
            logger.error(f"Erro ao extrair endereço: {e}")
            
            # Fallback: usar dados do Places se disponível
            return {
                "street": "",
                "number": "",
                "neighborhood": "",
                "city": "",
                "state": "",
                "full_address": best_match.get("address", "Endereço não disponível"),
                "confidence": 0.5,
                "source": "fallback",
                "coordinates": {"lat": lat, "lon": lon}
            }


if __name__ == "__main__":
    # Teste do agente
    import sys
    logging.basicConfig(level=logging.INFO)
    
    print("ValidationAgent - Teste de validação")
    
    # Mock de dados para teste
    query_analysis = {
        "architecture": {"style": "moderno", "floors_visible": 2},
        "distinctive_features": {"gate_type": "grade"},
        "urban_context": {"street_type": "residencial"}
    }
    
    sv_analysis = {
        "architecture": {"style": "moderno", "floors_visible": 2},
        "distinctive_features": {"gate_type": "grade"},
        "urban_context": {"street_type": "residencial"}
    }
    
    agent = ValidationAgent()
    
    validation = agent._validate_match(
        query_analysis,
        sv_analysis,
        -23.6505,
        -46.6815,
        0.85
    )
    
    print("\n✅ Resultado da validação:")
    print(json.dumps(validation, indent=2, ensure_ascii=False))
