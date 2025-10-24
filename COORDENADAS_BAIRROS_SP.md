# 📍 Coordenadas de Bairros de São Paulo

## 🎯 Uso Direto com Coordenadas

Se a geocodificação do bairro falhar, use coordenadas diretas:

```python
from main import GeoLocalizador

geo = GeoLocalizador()
resultado = geo.localizar_imovel(
    foto_path="foto.jpg",
    cidade="São Paulo",
    bairro="Santo Amaro",  # Nome para referência
    center_lat=-23.6505,   # Coordenadas do bairro
    center_lon=-46.7085,
    radius_m=3000
)
```

---

## 📋 Coordenadas dos Principais Bairros de SP

### **Zona Sul**

| Bairro | Latitude | Longitude | Código |
|--------|----------|-----------|--------|
| **Santo Amaro** | -23.6505 | -46.7085 | `center_lat=-23.6505, center_lon=-46.7085` |
| Moema | -23.6000 | -46.6650 | `center_lat=-23.6000, center_lon=-46.6650` |
| Brooklin | -23.6050 | -46.6950 | `center_lat=-23.6050, center_lon=-46.6950` |
| Vila Mariana | -23.5880 | -46.6380 | `center_lat=-23.5880, center_lon=-46.6380` |
| Jabaquara | -23.6400 | -46.6420 | `center_lat=-23.6400, center_lon=-46.6420` |
| Campo Belo | -23.6200 | -46.6750 | `center_lat=-23.6200, center_lon=-46.6750` |
| Chácara Santo Antônio | -23.6300 | -46.7100 | `center_lat=-23.6300, center_lon=-46.7100` |

### **Zona Oeste**

| Bairro | Latitude | Longitude | Código |
|--------|----------|-----------|--------|
| Pinheiros | -23.5650 | -46.6900 | `center_lat=-23.5650, center_lon=-46.6900` |
| Vila Madalena | -23.5550 | -46.6900 | `center_lat=-23.5550, center_lon=-46.6900` |
| Butantã | -23.5700 | -46.7200 | `center_lat=-23.5700, center_lon=-46.7200` |
| Lapa | -23.5280 | -46.7050 | `center_lat=-23.5280, center_lon=-46.7050` |
| Alto de Pinheiros | -23.5500 | -46.7050 | `center_lat=-23.5500, center_lon=-46.7050` |

### **Zona Norte**

| Bairro | Latitude | Longitude | Código |
|--------|----------|-----------|--------|
| Santana | -23.5050 | -46.6280 | `center_lat=-23.5050, center_lon=-46.6280` |
| Tucuruvi | -23.4800 | -46.6050 | `center_lat=-23.4800, center_lon=-46.6050` |
| Casa Verde | -23.5150 | -46.6650 | `center_lat=-23.5150, center_lon=-46.6650` |

### **Zona Leste**

| Bairro | Latitude | Longitude | Código |
|--------|----------|-----------|--------|
| Tatuapé | -23.5400 | -46.5750 | `center_lat=-23.5400, center_lon=-46.5750` |
| Mooca | -23.5550 | -46.5950 | `center_lat=-23.5550, center_lon=-46.5950` |
| Vila Formosa | -23.5650 | -46.5650 | `center_lat=-23.5650, center_lon=-46.5650` |

### **Centro**

| Bairro | Latitude | Longitude | Código |
|--------|----------|-----------|--------|
| Centro | -23.5505 | -46.6333 | `center_lat=-23.5505, center_lon=-46.6333` |
| Liberdade | -23.5600 | -46.6350 | `center_lat=-23.5600, center_lon=-46.6350` |
| Bela Vista | -23.5580 | -46.6450 | `center_lat=-23.5580, center_lon=-46.6450` |

---

## 🚀 Exemplo Completo: Santo Amaro

```python
# 1. Upload das fotos
from google.colab import files
uploaded = files.upload()
fotos = list(uploaded.keys())

# 2. Buscar com coordenadas diretas de Santo Amaro
from main import GeoLocalizador

geo = GeoLocalizador()
resultado = geo.localizar_imovel(
    foto_path=fotos[0],  # Ou use buscar_com_multiplas_fotos
    cidade="São Paulo",
    bairro="Santo Amaro",
    center_lat=-23.6505,  # Centro de Santo Amaro
    center_lon=-46.7085,
    radius_m=3000  # 3km de raio
)

# 3. Ver resultado
if resultado["success"]:
    print(f"🎉 ENCONTRADO!")
    print(f"📍 {resultado['endereco']}")
    print(f"🎯 Confiança: {resultado['confianca']:.1%}")
else:
    print(f"❌ {resultado['error']}")
```

---

## 🎯 Modo Híbrido (Recomendado)

Use múltiplas fotos + coordenadas diretas:

```python
from main import buscar_com_multiplas_fotos

# Não vai funcionar com buscar_com_multiplas_fotos diretamente
# Use o método tradicional com coordenadas:

from main import GeoLocalizador

geo = GeoLocalizador()

# Analisar primeira foto para escolher a melhor
# Depois buscar com coordenadas diretas
resultado = geo.localizar_imovel(
    foto_path="melhor_foto.jpg",
    cidade="São Paulo",
    bairro="Santo Amaro",
    center_lat=-23.6505,
    center_lon=-46.7085,
    radius_m=3000
)
```

---

## 📍 Como Pegar Coordenadas de Qualquer Local

### **Método 1: Google Maps**
1. Abra Google Maps
2. Procure o bairro/local
3. Clique com botão direito no centro
4. Clique em "Copiar coordenadas"
5. Cole no código: `center_lat=X, center_lon=Y`

### **Método 2: No Código**
```python
import requests

# Geocodificar manualmente
api_key = "SUA_CHAVE_GOOGLE"
endereco = "Santo Amaro, São Paulo, SP"

url = f"https://maps.googleapis.com/maps/api/geocode/json"
params = {"address": endereco, "key": api_key}

response = requests.get(url, params=params)
data = response.json()

if data["status"] == "OK":
    location = data["results"][0]["geometry"]["location"]
    print(f"center_lat={location['lat']}, center_lon={location['lng']}")
```

---

## 💡 Dicas

1. **Use coordenadas quando:**
   - Geocodificação falhar
   - Bairro tem nome ambíguo
   - Quer máxima precisão

2. **Raio recomendado:**
   - Bairro pequeno: 2000m
   - Bairro médio: 3000m
   - Bairro grande: 5000m

3. **Ajuste o raio se não encontrar:**
   ```python
   radius_m=5000  # Aumentar para 5km
   ```

---

## 🔧 Troubleshooting

### **"Não encontrou nada"**
```python
# Aumentar raio progressivamente
raios = [2000, 3000, 5000, 8000]

for raio in raios:
    print(f"Tentando raio: {raio}m")
    resultado = geo.localizar_imovel(
        foto_path="foto.jpg",
        cidade="São Paulo",
        center_lat=-23.6505,
        center_lon=-46.7085,
        radius_m=raio
    )
    if resultado["success"]:
        break
```

### **"Confiança baixa"**
- Use foto de melhor qualidade
- Tente outro ângulo
- Verifique se há Street View na região

---

**Use estas coordenadas para garantir que a busca funcione!** 📍✨
