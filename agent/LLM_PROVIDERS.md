# Configuración de Proveedores LLM 🤖

Este agente soporta múltiples proveedores de modelos de lenguaje para procesar los resultados de Karate.

## 📋 Proveedores Disponibles

| Proveedor | Costo | Velocidad | Configuración |
|-----------|-------|-----------|---------------|
| **Ollama** | 💰 Gratis | ⚡ Media | ⚡ Fácil (Local) |
| **OpenAI** | 💳 Pago | ⚡⚡ Rápido | ⚡⚡ API Key |
| **Azure OpenAI** | 💳 Pago | ⚡⚡ Rápido | ⚡ Azure |
| **Claude** | 💳 Pago | ⚡ Rápida | ⚡⚡ API Key |

---

## 🚀 Opción 1: Ollama (Gratuito - Recomendado)

### Ventajas
- ✅ 100% gratis
- ✅ Privacidad total (todo local)
- ✅ Sin límites de uso
- ✅ Modelos potentes: Llama3, Mistral

### Requisitos
- Windows/Mac/Linux
- 8GB+ RAM
- CPU decente (GPU mejor)

### Instalación

**1. Descargar e instalar Ollama:**
```
Windows: https://ollama.ai/download
```

**2. Instalar modelo Llama3:**
```bash
ollama pull llama3
```

**3. Configurar `.env`:**
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

**4. Probar:**
```bash
cd agent
python main.py ../target/karate-reports/karate-summary.json
```

### Modelos disponibles en Ollama:
- `llama3` (Recomendado)
- `mistral`
- `gemma`
- `phi3`

---

## 💳 Opción 2: OpenAI API

### Ventajas
- ✅ GPT-4o (muy potente)
- ✅ Rápido y confiable
- ✅ Fácil configuración

### Instalación

**1. Obtener API Key:**
```
https://platform.openai.com/api-keys
```

**2. Configurar `.env`:**
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o
```

**3. Configurar GitHub Secrets:**
```
OPENAI_API_KEY=sk-your-key-here
```

**Costo estimado:**
- ~$0.01 por cada 1K invocaciones
- Tu caso: ~$0.50/mes (si usas mucho)

---

## 🔵 Opción 3: Azure OpenAI

### Ventajas
- ✅ Integración con Azure
- ✅ Seguridad enterprise
- ✅ Puedes tener contrato corporativo

### Instalación

**1. Crear recurso Azure OpenAI:**
```
https://portal.azure.com/#create/Microsoft.CognitiveServicesOpenAI
```

**2. Configurar `.env`:**
```env
LLM_PROVIDER=azure
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
```

---

## 🟣 Opción 4: Anthropic Claude

### Ventajas
- ✅ Claude 3 Opus (excelente calidad)
- ✅ Contexto largo
- ✅ Buen para análisis complejo

### Instalación

**1. Obtener API Key:**
```
https://console.anthropic.com/
```

**2. Configurar `.env`:**
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-3-opus-20240229
```

---

## 📊 Comparación para tu Caso de Uso

Para procesar resultados de Karate (texto estructurado):

| Proveedor | Calidad | Costo | Recomendación |
|-----------|---------|-------|---------------|
| Ollama | 🔸🔸 | 💰 $0 | **Empieza con este** |
| OpenAI | 🔥🔥🔥 | 💳 $ | Si necesitas máxima calidad |
| Azure | 🔥🔥🔥 | 💳 $ | Si tu empresa usa Azure |
| Claude | 🔥🔥🔥 | 💳 $$ | Análisis muy complejo |

---

## 🔧 Cambiar de Proveedor

Solo cambia `LLM_PROVIDER` en `.env`:

```bash
# De Ollama a OpenAI
sed -i 's/LLM_PROVIDER=ollama/LLM_PROVIDER=openai/' agent/.env

# De OpenAI a Claude
sed -i 's/LLM_PROVIDER=openai/LLM_PROVIDER=anthropic/' agent/.env
```

---

## 🐛 Troubleshooting

### Ollama: Connection refused
```bash
# Verificar que Ollama está corriendo
curl http://localhost:11434/api/generate -d '{
  "model": "llama3",
  "prompt": "Hi"
}'
```

### OpenAI: Invalid API Key
```bash
# Verificar que la key está correcta
echo $OPENAI_API_KEY | head -c 20
```

### CUDA Out of Memory (Ollama)
```bash
# Usar modelo más pequeño
ollama pull phi3
# Cambiar en .env: OLLAMA_MODEL=phi3
```

---

## 💡 Recomendación Final

**Para empezar:**
1. Instala Ollama (gratis)
2. Usa modelo `llama3`
3. Si necesitas más calidad → OpenAI
4. Si tienes Azure corporativo → Azure OpenAI

**El código ya está preparado para cualquiera de las opciones** 🚀
