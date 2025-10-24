# 🔧 Setup Completo - Passo a Passo

## 📋 Checklist Pré-Execução

- [ ] Chave Google Cloud API (Places + Street View)
- [ ] Chave OpenAI API (GPT-4o)
- [ ] Python 3.10+ instalado
- [ ] Foto do imóvel preparada
- [ ] Coordenadas aproximadas (lat/lon)

---

## 1️⃣ Configurar Google Cloud Platform

### Passo 1: Criar Projeto
1. Acesse [console.cloud.google.com](https://console.cloud.google.com/)
2. Clique em "Selecionar projeto" → "Novo projeto"
3. Nome: `geolocalizacao-imoveis`
4. Clique em "Criar"

### Passo 2: Habilitar APIs
1. No menu lateral: **APIs e serviços** → **Biblioteca**
2. Busque e habilite (uma por vez):
   - **Places API (New)**
   - **Street View Static API**
   - **Street View Metadata API**

### Passo 3: Criar API Key
1. **APIs e serviços** → **Credenciais**
2. **Criar credenciais** → **Chave de API**
3. Copie a chave gerada

### Passo 4: Configurar Billing
1. Menu lateral: **Faturamento**
2. **Vincular conta de faturamento**
3. Adicione cartão de crédito

**💰 Custos Estimados:**
- Places API: $17 por 1000 requests
- Street View Static: $7 por 1000 imagens
- **Por busca:** ~$2.50-7.00 (200-500 requests)

---

## 2️⃣ Configurar OpenAI (GPT-4o)

### Passo 1: Criar Conta
1. Acesse [platform.openai.com](https://platform.openai.com/)
2. Crie conta com email
3. Verifique email

### Passo 2: Adicionar Créditos
1. Menu: **Settings** → **Billing**
2. **Add payment method**
3. Adicione créditos (mínimo $5)

### Passo 3: Gerar API Key
1. Menu: **API Keys**
2. **Create new secret key**
3. Nome: `geolocalizacao`
4. Copie a chave (só aparece uma vez!)

**💰 Custos:** ~$0.20-0.80 por busca (GPT-4o é mais barato que Claude)

---

## 3️⃣ Instalar Projeto

```bash
cd geolocaliza
pip install -r requirements.txt
```

**Tempo estimado:** 2-5 minutos

---

## 4️⃣ Configurar .env

Crie arquivo `.env` na pasta `geolocaliza/`:

```env
GOOGLE_API_KEY=sua_chave_google_aqui
OPENAI_API_KEY=sua_chave_openai_aqui
```

---

## 5️⃣ Primeira Execução

```bash
python main.py \
  --foto casa.jpg \
  --cidade "São Paulo" \
  --bairro "Alto da Boa Vista" \
  --lat -23.6505 \
  --lon -46.6815 \
  --raio 2000
```

**Tempo esperado:** 2-5 minutos

---

## ✅ Pronto!

Veja os resultados em `output/`:
- `resultado_final.json` - Endereço completo
- `mapa.html` - Mapa interativo
- `candidatos_validados.csv` - Top matches

Para mais detalhes, consulte `GUIA_EXECUCAO.md`
