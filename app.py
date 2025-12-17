import streamlit as st
import openai
import json
import base64
from PIL import Image
import io

# --- ページ設定 ---
st.set_page_config(
    page_title="AdPrompt AI - Digital Signage Creator",
    page_icon="🍌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- カスタムCSS ---
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
        font-weight: bold;
        padding: 0.5rem 1rem;
        border-radius: 10px;
    }
    .reportview-container {
        background: #f0f2f6;
    }
    h1 { color: #1E1E1E; }
    h3 { color: #333333; border-bottom: 2px solid #FF4B4B; padding-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 関数定義 ---

def get_api_key():
    """SecretsからAPIキーを取得する"""
    try:
        return st.secrets["OPENAI_API_KEY"]
    except KeyError:
        st.error("🚨 API Keyが設定されていません。.streamlit/secrets.toml を確認してください。")
        return None

def encode_image(image_file):
    """画像をBase64エンコードする"""
    if image_file is not None:
        bytes_data = image_file.getvalue()
        return base64.b64encode(bytes_data).decode('utf-8')
    return None

def generate_json_prompt(api_key, product_info, target_info, design_info, image_base64=None):
    """GPT-4oでJSONプロンプトを生成する"""
    client = openai.OpenAI(api_key=api_key)
    
    # JSONスキーマ定義
    schema_structure = """
    {
        "product_name": "String",
        "target_audience": "String",
        "concept_rationale": "String",
        "nano_banana_pro_prompt": {
            "prompt": "String (Detailed English Prompt for DALL-E 3)",
            "negative_prompt": "String",
            "aspect_ratio": "String",
            "layout_template": "String",
            "color_palette": ["Hex1", "Hex2", "Hex3"],
            "mood": "String"
        }
    }
    """

    system_instruction = f"""
    You are an Ace Creative Director at WPP Group.
    Create a highly effective image generation prompt (JSON) for convenience store digital signage.
    
    STRICT OUTPUT FORMAT:
    You MUST output a valid JSON object strictly following this structure:
    {schema_structure}
    
    IMPORTANT for Image Generation:
    The 'prompt' field must be optimized for DALL-E 3. It should be descriptive, specifying lighting, camera angle, and textures.
    Exclude text rendering instructions as DALL-E struggle with specific Japanese text. Focus on visual impact.
    """

    user_content = [
        {
            "type": "text",
            "text": f"""
            Generate a JSON prompt for:
            [Product] {product_info['name']} - {product_info['features']}
            [Target] {target_info['age']}yo {target_info['gender']}, Income:{target_info['income']}, Type:{target_info['repeat_type']}
            [Design] {design_info['orientation']}, Layout: {design_info['layout']}
            """
        }
    ]

    if image_base64:
        user_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
        })
        user_content[0]["text"] += "\nRefer to the attached image for product appearance."

    response = client.chat.completions.create(
        model="gpt-4o", 
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_content}
        ],
        response_format={"type": "json_object"},
        temperature=0.7
    )
    return response.choices[0].message.content

def generate_image_dalle3(api_key, prompt_text, orientation):
    """DALL-E 3で画像を生成する"""
    client = openai.OpenAI(api_key=api_key)
    
    # DALL-E 3のサイズ指定 (Standard / Wide / Tall)
    if "横長" in orientation:
        size = "1792x1024" # 16:9に近いワイド
    elif "縦長" in orientation:
        size = "1024x1792" # 9:16に近いトール
    else:
        size = "1024x1024"

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt_text,
        size=size,
        quality="standard",
        n=1,
    )
    return response.data[0].url

# --- サイドバー ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=80)
    st.title("Settings")
    st.markdown("API Key is managed via Secrets.")
    st.info("""
    **Developer:** WPP Creative Logic Module
    **Target:** Nano Banana Pro + DALL-E 3
    """)

# --- メインエリア ---
st.title("🍌 Nano Banana Pro: Ad Creator")
st.caption("Auto-Generate Prompts & Visuals for Digital Signage")

api_key = get_api_key()

with st.form("main_form"):
    st.subheader("1. Product Information")
    col1, col2 = st.columns([1, 1])
    with col1:
        product_name = st.text_input("商品名", placeholder="例: プレミアム濃厚プリン")
        product_features = st.text_area("商品特徴", placeholder="例: 金色のパッケージ、シズル感、高級感", height=100)
    with col2:
        uploaded_file = st.file_uploader("商品画像 (任意)", type=['png', 'jpg', 'jpeg'])
        if uploaded_file:
            st.image(uploaded_file, caption="Ref Image", width=150)

    st.markdown("---")
    st.subheader("2. Target & Design")
    col_a, col_b = st.columns(2)
    with col_a:
        age = st.number_input("年齢", 30, step=5)
        income = st.selectbox("収入", ["High", "Medium", "Low"], index=1)
        gender = st.radio("性別", ["男性", "女性", "その他"], horizontal=True)
        repeat_type = st.selectbox("タイプ", ["新規層", "リピーター"])
    with col_b:
        orientation = st.selectbox("向き", ["横長 (16:9)", "縦長 (9:16)"])
        layout = st.selectbox("レイアウト", ["全面画像", "テキスト重視", "4分割グリッド", "シズル感重視"])

    aspect_ratio = "16:9" if "横長" in orientation else "9:16"
    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.form_submit_button("Generate Creative & Image 🚀")

if submitted and api_key:
    if not product_name:
        st.warning("商品名を入力してください。")
    else:
        p_info = {"name": product_name, "features": product_features}
        t_info = {"age": age, "gender": gender, "income": income, "repeat_type": repeat_type}
        d_info = {"orientation": orientation, "aspect_ratio": aspect_ratio, "layout": layout}
        img_b64 = encode_image(uploaded_file) if uploaded_file else None
        
        # 進行状況コンテナ
        status_container = st.status("💡 WPP Ace Creative Director is working...", expanded=True)
        
        try:
            # 1. プロンプト生成 (GPT-4o)
            status_container.write("1. Brainstorming & Generating Prompt...")
            json_result_str = generate_json_prompt(api_key, p_info, t_info, d_info, img_b64)
            json_data = json.loads(json_result_str)
            
            # データの安全な取得
            final_data = json_data.get('nano_banana_pro_prompt', json_data)
            prompt_text = final_data.get('prompt', '')

            if not prompt_text:
                raise ValueError("Prompt text not found in JSON response")

            status_container.write("✅ Prompt Generated!")

            # 2. 画像生成 (DALL-E 3)
            status_container.write("2. Generating Image with DALL-E 3 (This takes a moment)...")
            image_url = generate_image_dalle3(api_key, prompt_text, orientation)
            
            status_container.update(label="✨ All Processes Complete!", state="complete", expanded=False)

            # --- 結果表示 ---
            st.success("生成完了しました")
            
            # 上段: 画像
            st.subheader("🖼️ Generated Creative")
            st.image(image_url, caption=f"Generated for: {product_name}", use_column_width=True)

            # 下段: 2カラム詳細
            res_col1, res_col2 = st.columns(2)
            
            with res_col1:
                st.markdown("### 🎨 Strategy & Prompt")
                st.info(f"**Target:** {json_data.get('target_audience', 'N/A')}")
                st.write(f"**Rationale:** {json_data.get('concept_rationale', 'N/A')}")
                st.text_area("Generated English Prompt", prompt_text, height=150)

            with res_col2:
                st.markdown("### 📋 JSON Data")
                st.code(json.dumps(final_data, indent=4), language='json')
                st.download_button(
                    label="Download JSON",
                    data=json.dumps(final_data, indent=4),
                    file_name="nano_banana_prompt.json",
                    mime="application/json"
                )

        except Exception as e:
            status_container.update(label="❌ Error Occurred", state="error")
            st.error(f"エラーが発生しました: {e}")
            if 'json_result_str' in locals():
                with st.expander("Raw Response for Debug"):
                    st.text(json_result_str)
