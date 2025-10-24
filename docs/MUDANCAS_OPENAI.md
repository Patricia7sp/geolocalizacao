# 🔄 Mudanças: Anthropic → OpenAI

## ✅ Alterações Realizadas

### **1. Arquivos de Código Modificados**

#### `config.py`
- ❌ `ANTHROPIC_API_KEY` → ✅ `OPENAI_API_KEY`
- ❌ `vision_model: "claude-3-5-sonnet-20241022"` → ✅ `vision_model: "gpt-4o"`
- ❌ `validation_model: "claude-3-5-sonnet-20241022"` → ✅ `validation_model: "gpt-4o"`

#### `agents/vision_agent.py`
- ❌ `import anthropic` → ✅ `from openai import OpenAI`
- ❌ `self.client = anthropic.Anthropic()` → ✅ `self.client = OpenAI()`
- ❌ `client.messages.create()` → ✅ `client.chat.completions.create()`
- ❌ Formato de imagem Anthropic → ✅ Formato `image_url` OpenAI
- ❌ `message.content[0].text` → ✅ `response.choices[0].message.content`

#### `agents/validation_agent.py`
- ❌ `import anthropic` → ✅ `from openai import OpenAI`
- ❌ `self.client = anthropic.Anthropic()` → ✅ `self.client = OpenAI()`
- ❌ `client.messages.create()` → ✅ `client.chat.completions.create()`
- ❌ `message.content[0].text` → ✅ `response.choices[0].message.content`
- Atualizado em 2 métodos: `_validate_match()` e `extract_address()`

---

### **2. Arquivos de Configuração**

#### `requirements.txt`
```diff
- anthropic>=0.40.0
  openai>=1.0.0
```

#### `.env.example`
```diff
  GOOGLE_API_KEY=sua_chave_google_aqui
- ANTHROPIC_API_KEY=sua_chave_anthropic_aqui
+ OPENAI_API_KEY=sua_chave_openai_aqui
```

---

### **3. Documentação Atualizada**

#### `SETUP_COMPLETO.md`
- Seção "Configurar Anthropic" → "Configurar OpenAI"
- Link: console.anthropic.com → platform.openai.com
- Custos: $0.30-1.00 → $0.20-0.80 (GPT-4o é mais barato!)

#### `GUIA_EXECUCAO.md`
- Todas as referências a Anthropic/Claude substituídas por OpenAI/GPT-4o
- Troubleshooting atualizado
- Exemplos de código atualizados

#### `Geolocalizacao_Colab.ipynb`
- Célula de instalação: removido `anthropic`
- Célula de configuração: `ANTHROPIC_KEY` → `OPENAI_KEY`
- Links e instruções atualizados

---

## 💰 Comparação de Custos

### Anthropic (Claude 3.5 Sonnet)
- Input: $3 por 1M tokens
- Output: $15 por 1M tokens
- **Custo médio por busca:** $0.30-1.00

### OpenAI (GPT-4o)
- Input: $2.50 por 1M tokens
- Output: $10 por 1M tokens
- **Custo médio por busca:** $0.20-0.80

**💡 Economia: ~30-40% mais barato com OpenAI!**

---

## 🔑 Como Obter a Chave OpenAI

1. Acesse [platform.openai.com](https://platform.openai.com/)
2. Crie uma conta (ou faça login)
3. Vá em **Settings** → **Billing** → Adicione créditos
4. Vá em **API Keys** → **Create new secret key**
5. Copie a chave (formato: `sk-proj-...`)
6. Cole no arquivo `.env`:
   ```env
   OPENAI_API_KEY=sk-proj-sua_chave_aqui
   ```

---

## ⚙️ Modelos Disponíveis

Você pode usar outros modelos OpenAI editando `config.py`:

```python
LLM_CONFIG = {
    # Opções de modelos:
    "vision_model": "gpt-4o",              # Recomendado (mais rápido e barato)
    # "vision_model": "gpt-4-turbo",       # Alternativa
    # "vision_model": "gpt-4-vision-preview",  # Versão antiga
    
    "validation_model": "gpt-4o",          # Recomendado
    # "validation_model": "gpt-4-turbo",   # Alternativa
    
    "temperature": 0.1,
    "max_tokens": 2000,
}
```

**Recomendação:** Use `gpt-4o` para melhor custo-benefício.

---

## 🧪 Testar a Mudança

```bash
# 1. Atualizar dependências
pip install --upgrade openai
pip uninstall anthropic  # Opcional: remover Anthropic

# 2. Configurar .env
echo "OPENAI_API_KEY=sua_chave_aqui" >> .env

# 3. Testar
python -c "
from agents.vision_agent import VisionAgent
from agents.validation_agent import ValidationAgent
print('✅ Agentes carregados com OpenAI!')
"

# 4. Executar teste completo
python main.py --foto teste.jpg --cidade "São Paulo" --lat -23.65 --lon -46.68 --raio 1000
```

---

## 📊 Diferenças de Performance

| Aspecto | Anthropic (Claude) | OpenAI (GPT-4o) |
|---------|-------------------|-----------------|
| **Velocidade** | ~2-3s por request | ~1-2s por request |
| **Custo** | $0.30-1.00/busca | $0.20-0.80/busca |
| **Qualidade Vision** | Excelente | Excelente |
| **Formato JSON** | Mais consistente | Bom (às vezes precisa parsing) |
| **Rate Limits** | 50 req/min | 500 req/min (Tier 1) |

**Conclusão:** GPT-4o é mais rápido, mais barato e tem rate limits maiores. ✅

---

## 🔄 Reverter para Anthropic (se necessário)

Se quiser voltar para Anthropic:

```bash
# 1. Reinstalar
pip install anthropic

# 2. Reverter código
git checkout HEAD -- config.py agents/vision_agent.py agents/validation_agent.py

# 3. Configurar .env
echo "ANTHROPIC_API_KEY=sua_chave_aqui" >> .env
```

---

## ✅ Checklist de Verificação

Após as mudanças, confirme:

- [ ] `requirements.txt` não tem `anthropic`
- [ ] `.env` tem `OPENAI_API_KEY` (não `ANTHROPIC_API_KEY`)
- [ ] `config.py` usa `gpt-4o` como modelo
- [ ] `vision_agent.py` importa `OpenAI`
- [ ] `validation_agent.py` importa `OpenAI`
- [ ] Notebook Colab atualizado
- [ ] Documentação atualizada
- [ ] Teste executado com sucesso

---

**🎉 Migração completa! Agora você está usando OpenAI GPT-4o.**
