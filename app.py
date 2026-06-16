from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import anthropic
import os
import base64

app = Flask(__name__, static_folder='static')
CORS(app)

client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        asset    = data.get('asset', 'WIN')
        tf       = data.get('tf', '5min')
        price    = data.get('price', '')
        htf      = data.get('htf', '')
        trend    = data.get('trend', '')
        sup      = data.get('sup', '')
        res      = data.get('res', '')
        note     = data.get('note', '')
        image_b64= data.get('image', None)

        asset_labels = {
            'WIN':    'Mini Índice Futuro (WIN)',
            'EURUSD': 'EUR/USD',
            'USDJPY': 'USD/JPY',
        }
        asset_label = asset_labels.get(asset, asset)

        if image_b64:
            # Análise por imagem
            prompt = f"""Você é trader profissional especialista em análise técnica.
Analise esta imagem do gráfico de {asset_label} no timeframe de {tf}.
Preço atual informado: {price or 'não informado'}
Observação do trader: {note or 'nenhuma'}

Analise: tendência, padrões de candle, médias móveis, suporte/resistência, momentum.
Responda APENAS JSON puro sem markdown:
{{"verdict":"ENTRAR" ou "AGUARDAR" ou "EVITAR","confidence":número 0-100,"entry":"nível de entrada","stop":"stop loss","target":"take profit","rr":"número ex: 2.3","reason":"2-3 frases simples em português","bulls":["fator positivo"],"bears":["fator negativo"],"tip":"conselho direto"}}"""

            messages = [{
                'role': 'user',
                'content': [
                    {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg', 'data': image_b64}},
                    {'type': 'text', 'text': prompt}
                ]
            }]
        else:
            # Análise por dados
            prompt = f"""Você é trader profissional sênior especializado em análise técnica intraday.
ATIVO: {asset_label}
TIMEFRAME: {tf}
VIÉS TIMEFRAME MAIOR: {htf or 'não informado'}
PREÇO ATUAL: {price}
DIREÇÃO ATUAL: {trend or 'não informado'}
SUPORTE: {sup or 'não informado'}
RESISTÊNCIA: {res or 'não informado'}
OBSERVAÇÃO: {note or 'nenhuma'}

Analise confluência entre timeframes, posição em relação a S/R, e qualidade do setup.
Responda APENAS JSON puro sem markdown:
{{"verdict":"ENTRAR" ou "AGUARDAR" ou "EVITAR","confidence":número 0-100,"entry":"nível de entrada","stop":"stop loss","target":"take profit","rr":"número ex: 2.3","reason":"2 frases simples em português","bulls":["fator positivo 1","fator 2"],"bears":["fator negativo"],"tip":"conselho direto"}}"""

            messages = [{'role': 'user', 'content': prompt}]

        response = client.messages.create(
            model='claude-sonnet-4-20250514',
            max_tokens=900,
            messages=messages
        )

        txt = ''.join(block.text for block in response.content if hasattr(block, 'text'))
        txt = txt.replace('```json', '').replace('```', '').strip()

        import json
        result = json.loads(txt)
        return jsonify({'ok': True, 'result': result})

    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
