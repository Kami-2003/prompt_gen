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

# --- カスタムCSS (UIの微調整) ---
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
    h1 {
        color: #1E1E1E;
    }
    h3 {
        color: #333333;
        border-bottom: 2px solid #FF4B4B;
        padding-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 関数定義 ---

def encode_image(image_file):
    """画像をBase64エンコードする"""
    if image_file is not None:
        bytes_data = image_file.getvalue()
        return base64.b64encode(bytes_data).decode('utf-8')
    return None

def generate_prompt(api_key, product_info, target_info, design_info, image_base64=None):
    """OpenAI APIを呼び出してJSONプロンプトを生成する"""
    
    client = openai.OpenAI(api_key=api_key)
    
    # JSONスキーマ定義
    json_schema = {
        "product_name": product_info['name'],
        "target_audience": f"{target_info['age']} years old, {target_info['gender']}",
        "concept_rationale": "Reasoning for the design choice (WPP Ace perspective)",
        "nano_banana_pro_prompt": {
            "prompt": "Highly detailed English prompt for image generation...",
            "negative_prompt": "Low quality, blurry, text, watermark...",
            "aspect_ratio": design_info['aspect_ratio'],
            "layout_template": design_info['layout'],
            "color_palette": ["#Hex1", "#Hex2", "#Hex3"],
            "mood": "Energetic / Calm / Luxury etc."
        }
    }

    # システムプロンプト：WPPエース社員の人格
    system_instruction = """
    You are an Ace Creative Director at the WPP Group, specializing in Digital Out-of-Home (DOOH) advertising for convenience stores.
    
    Your Mission:
    Create a highly effective image generation prompt (JSON format) for a product to be displayed on a convenience store digital signage.
    
    Key Considerations:
    1. **Context**: Convenience store customers decide in < 1 second. High visibility and appetizing/appealing visuals are crucial.
    2. **Targeting**: Analyze the Age, Gender, Income, and Repeat Rate to determine the optimal color psychology, lighting, and composition.
    3. **Output**: You must output ONLY valid JSON matching the provided schema. The 'prompt' field should be in English, highly descriptive, focusing on lighting, textures, and composition tailored for AI image generators (like Midjourney or Stable Diffusion).
    """

    # ユーザープロンプトの構築
    user_content = [
        {
            "type": "text",
            "text": f"""
            Please generate a JSON prompt based on the following inputs:
            
            [Product Info]
            - Name: {product_info['name']}
            - Features: {product_info['features']}
            
            [Target Audience]
            - Age: {target_info['age']}
            - Gender: {target_info['gender']}
            - Income: {target_info['income']}
            - Type: {target_info['repeat_type']}
            
            [Design Specs]
            - Orientation: {design_info['orientation']} (Set aspect_ratio to {design_info['aspect_ratio']})
            - Layout: {design_info['layout']}
            """
        }
    ]

    # 画像がある場合はVision用のメッセージを追加
    if image_base64:
        user_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_base64}"
            }
        })
        user_content[0]["text"] += "\n[Visual Reference]\nRefer to the attached product image for color accuracy and packaging details."

    try:
        response = client.chat.completions.create(
            model="gpt-4o", # Vision機能と高いJSON生成能力のためGPT-4o推奨
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        raise e

# --- サイドバー: 設定 ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=80)
    st.title("Settings")
    
    api_key = st.text_input("OpenAI API Key", type="password", help="Start with sk-...")
    
    st.markdown("---")
    st.info("""
    **Developer:** WPP Creative Logic Module
    **Version:** 1.0.0
    **Target:** Nano Banana Pro
    """)

# --- メインエリア ---
st.title("🍌 Nano Banana Pro: Ad Prompt Generator")
st.caption("Convenience Store Digital Signage Optimization Tool")

# フォームエリア
with st.form("main_form"):
    
    # 1. 商品情報
    st.subheader("1. Product Information")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        product_name = st.text_input("商品名", placeholder="例: プレミアム濃厚プリン")
        product_features = st.text_area("商品特徴・訴求ポイント", placeholder="例: 北海道産生クリーム使用、とろける食感、自分へのご褒美、金色のパッケージ", height=100)
    
    with col2:
        uploaded_file = st.file_uploader("商品画像 (任意)", type=['png', 'jpg', 'jpeg'], help="AIが画像を解析し、パッケージや色味を忠実に再現しようとします。")
        if uploaded_file:
            st.image(uploaded_file, caption="Reference Image", width=200)

    st.markdown("---")

    # 2. ターゲット & デザイン
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("2. Target Audience")
        c1, c2 = st.columns(2)
        with c1:
            age = st.number_input("年齢層", min_value=10, max_value=90, value=30, step=5)
            income = st.selectbox("収入層", ["High", "Medium", "Low"], index=1)
        with c2:
            gender = st.radio("性別", ["男性", "女性", "その他"], horizontal=True)
            repeat_type = st.selectbox("顧客タイプ", ["新規層 (Attention重視)", "リピーター (Recall重視)"])

    with col_b:
        st.subheader("3. Design Configuration")
        orientation = st.selectbox("画面の向き", ["横長 (Landscape 16:9)", "縦長 (Portrait 9:16)"])
        layout = st.selectbox("レイアウト構成", ["全面画像 (Full Image)", "テキスト重視 (Text Heavy)", "4分割グリッド (4-Grid)", "3分割 (Split)", "シズル感重視 (Sizzle Focus)"])

    # ロジック変換
    aspect_ratio = "16:9" if "横長" in orientation else "9:16"
    
    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.form_submit_button("Generate Creative Prompt 🚀")

# --- 結果表示エリア ---
if submitted:
    if not api_key:
        st.error("⚠️ OpenAI API Keyを入力してください。")
    elif not product_name:
        st.warning("⚠️ 商品名を入力してください。")
    else:
        # 入力データの整理
        p_info = {"name": product_name, "features": product_features}
        t_info = {"age": age, "gender": gender, "income": income, "repeat_type": repeat_type}
        d_info = {"orientation": orientation, "aspect_ratio": aspect_ratio, "layout": layout}
        
        # 画像処理
        img_b64 = encode_image(uploaded_file) if uploaded_file else None
        
        # 処理中の表示
        with st.status("💡 WPP Ace Creative Director is brainstorming...", expanded=True) as status:
            st.write("Analyzing target demographics...")
            st.write("Defining color psychology for convenience store environment...")
            st.write("Drafting visual composition...")
            
            try:
                # APIコール
                json_result_str = generate_prompt(api_key, p_info, t_info, d_info, img_b64)
                
                # JSONパース
                json_data = json.loads(json_result_str)
                
                status.update(label="✅ Generation Complete!", state="complete", expanded=False)
                
                # 結果表示
                st.success("プロンプト生成に成功しました")
                
                # 2カラムで解説とJSONを表示
                res_col1, res_col2 = st.columns([1, 1])
                
                with res_col1:
                    st.markdown("### 🎨 Creative Strategy")
                    st.info(f"**Target Analysis:**\n{json_data.get('target_audience')}")
                    st.write(f"**Concept Rationale:**\n{json_data.get('concept_rationale')}")
                    
                    # カラーパレットの可視化 (もしJSONに含まれていれば)
                    if "color_palette" in json_data["nano_banana_pro_prompt"]:
                        st.write("**Recommended Colors:**")
                        cols = st.columns(len(json_data["nano_banana_pro_prompt"]["color_palette"]))
                        for idx, color in enumerate(json_data["nano_banana_pro_prompt"]["color_palette"]):
                            cols[idx].color_picker(f"Color {idx+1}", color, disabled=True)

                with res_col2:
                    st.markdown("### 📋 JSON Output (Nano Banana Pro)")
                    st.code(json.dumps(json_data["nano_banana_pro_prompt"], indent=4), language='json')
                    
                    # コピー用など
                    st.download_button(
                        label="Download JSON",
                        data=json.dumps(json_data["nano_banana_pro_prompt"], indent=4),
                        file_name="nano_banana_prompt.json",
                        mime="application/json"
                    )

            except openai.AuthenticationError:
                st.error("🚫 API Keyが無効です。正しいキーを確認してください。")
            except openai.APIConnectionError:
                st.error("🔌 通信エラーが発生しました。ネットワーク接続を確認してください。")
            except Exception as e:
                st.error(f"❌ 予期せぬエラーが発生しました: {e}")
