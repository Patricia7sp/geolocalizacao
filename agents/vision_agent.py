"""
Agente 1: Análise Visual com OpenAI Vision
Extrai características detalhadas da foto do imóvel
"""

import base64
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from openai import OpenAI
from PIL import Image
import io

from config import LLM_CONFIG, PROMPTS, OPENAI_API_KEY

logger = logging.getLogger(__name__)


class VisionAgent:
    """
    Agente responsável pela análise visual profunda da foto do imóvel.
    Usa OpenAI Vision para extrair características arquitetônicas e contextuais.
    """
    
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY não configurada. Crie arquivo .env")
        
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = LLM_CONFIG["vision_model"]
        logger.info(f"VisionAgent inicializado com modelo {self.model}")
    
    def analyze_image(self, image_path: str | Path) -> Dict[str, Any]:
        """
        Analisa uma imagem e retorna características estruturadas.
        
        Args:
            image_path: Caminho para a imagem
            
        Returns:
            Dict com análise estruturada (architecture, distinctive_features, etc.)
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise FileNotFoundError(f"Imagem não encontrada: {image_path}")
        
        logger.info(f"Analisando imagem: {image_path.name}")
        
        # Carregar e codificar imagem
        image_data = self._load_and_encode_image(image_path)
        
        # Fazer requisição ao OpenAI
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=LLM_CONFIG["max_tokens"],
                temperature=LLM_CONFIG["temperature"],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{image_data['media_type']};base64,{image_data['data']}"
                                }
                            },
                            {
                                "type": "text",
                                "text": PROMPTS["visual_analysis"]
                            }
                        ],
                    }
                ],
            )
            
            # Extrair resposta
            response_text = response.choices[0].message.content
            
            # Parse JSON (remover possíveis markdown wrappers)
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            analysis = json.loads(response_text.strip())
            
            logger.info(f"Análise completa. Estilo: {analysis.get('architecture', {}).get('style', 'N/A')}")
            
            return {
                "success": True,
                "analysis": analysis,
                "raw_response": response_text,
                "image_path": str(image_path)
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao parsear JSON da resposta: {e}")
            logger.error(f"Resposta recebida: {response_text}")
            return {
                "success": False,
                "error": f"JSON inválido: {e}",
                "raw_response": response_text
            }
            
        except Exception as e:
            logger.error(f"Erro na API OpenAI: {e}")
            return {
                "success": False,
                "error": f"API Error: {e}"
            }
    
    def _load_and_encode_image(self, image_path: Path) -> Dict[str, str]:
        """
        Carrega imagem e converte para base64.
        Redimensiona se necessário para otimizar tokens.
        """
        # Abrir imagem
        img = Image.open(image_path)
        
        # Converter para RGB se necessário
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Redimensionar se muito grande (max 2048px no lado maior)
        max_size = 2048
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            logger.info(f"Imagem redimensionada para {new_size}")
        
        # Converter para base64
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return {
            "data": image_data,
            "media_type": "image/jpeg"
        }
    
    def extract_text_hints(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai dicas textuais úteis para busca geográfica.
        
        Returns:
            Dict com address_number, street_signs, condo_name
        """
        if not analysis.get("success"):
            return {}
        
        visible_text = analysis.get("analysis", {}).get("visible_text", {})
        
        hints = {
            "has_address_number": visible_text.get("address_number", "não visível") != "não visível",
            "address_number": visible_text.get("address_number"),
            "street_signs": visible_text.get("street_signs", []),
            "condo_name": visible_text.get("condo_name"),
            "other_text": visible_text.get("other_text", [])
        }
        
        logger.info(f"Dicas textuais: {hints}")
        return hints


if __name__ == "__main__":
    # Teste do agente
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Uso: python vision_agent.py <caminho_imagem>")
        sys.exit(1)
    
    agent = VisionAgent()
    result = agent.analyze_image(sys.argv[1])
    
    if result["success"]:
        print("\n✅ Análise bem-sucedida!")
        print(json.dumps(result["analysis"], indent=2, ensure_ascii=False))
        
        hints = agent.extract_text_hints(result)
        print("\n🔍 Dicas textuais:")
        print(json.dumps(hints, indent=2, ensure_ascii=False))
    else:
        print(f"\n❌ Erro: {result['error']}")
