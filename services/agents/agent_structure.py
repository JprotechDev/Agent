from google import genai
from pydantic import BaseModel
from dotenv import load_dotenv
import os

# Load biến môi trường
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
client = genai.Client(api_key=GOOGLE_API_KEY)

# ---------------------- Schema ----------------------

class Recipe(BaseModel):
    recipe_name: str
    ingredients: list[str]

class MenuSuggestion(BaseModel):
    day: str
    meals: list[str]

class QuickDish(BaseModel):
    dish_name: str
    prep_time_minutes: int
    ingredients: list[str]

# ---------------------- Hàm chức năng ----------------------

def get_cookie_recipes():
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Liệt kê một vài công thức bánh quy phổ biến, bao gồm cả nguyên liệu và số lượng cần thiết.",
        config={
            "response_mime_type": "application/json",
            "response_schema": list[Recipe],
        },
    )
    return response.parsed

def get_recipes_by_ingredient(ingredient: str = "trứng"):
    prompt = f"Liệt kê 3 món ăn có sử dụng '{ingredient}'. Bao gồm tên món và nguyên liệu."
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": list[Recipe],
        },
    )
    return response.parsed

def suggest_menu_for_week():
    prompt = "Gợi ý thực đơn cho cả tuần (Thứ 2 đến Chủ nhật), mỗi ngày gồm 3 bữa: sáng, trưa và tối."
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": list[MenuSuggestion],
        },
    )
    return response.parsed

def quick_dishes_under_15_minutes():
    prompt = "Liệt kê 3 món ăn có thể nấu trong vòng 15 phút. Gồm tên món, thời gian chuẩn bị và nguyên liệu."
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": list[QuickDish],
        },
    )
    return response.parsed

# ---------------------- Danh sách mô tả hàm ----------------------

functions = [
    {
        "name": "get_cookie_recipes",
        "description": "Liệt kê công thức bánh quy phổ biến.",
    },
    {
        "name": "get_recipes_by_ingredient",
        "description": "Tìm món ăn theo nguyên liệu được chỉ định.",
    },
    {
        "name": "suggest_menu_for_week",
        "description": "Gợi ý thực đơn cho 7 ngày trong tuần.",
    },
    {
        "name": "quick_dishes_under_15_minutes",
        "description": "Các món nấu nhanh dưới 15 phút.",
    }
]

# ---------------------- AI chọn hàm dựa vào mô tả ----------------------

def select_function_by_ai(user_input: str) -> str:
    function_descriptions = "\n".join(
        [f"{f['name']}: {f['description']}" for f in functions]
    )

    selection_prompt = (
        f"Người dùng yêu cầu: \"{user_input}\"\n"
        f"Dưới đây là danh sách các hàm có sẵn:\n{function_descriptions}\n\n"
        f"Hãy chọn tên hàm phù hợp nhất để xử lý yêu cầu trên. Trả về *duy nhất* tên hàm (không có giải thích)."
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=selection_prompt
    )
    return response.text.strip()

# ---------------------- Main Logic ----------------------

if __name__ == "__main__":
    print("💬 Nhập yêu cầu bằng tiếng Việt (ví dụ: 'Gợi ý thực đơn cho tuần', 'Món có trứng', 'Món nấu nhanh')")
    user_query = input("🔍 Yêu cầu của bạn: ")

    selected_func = select_function_by_ai(user_query)
    print(f"\n🤖 Hàm được chọn: {selected_func}")

    try:
        if selected_func == "get_cookie_recipes":
            result = get_cookie_recipes()
        elif selected_func == "get_recipes_by_ingredient":
            # Trích xuất từ khóa đơn giản (nâng cấp thêm nếu muốn)
            keyword = user_query.split()[-1]
            result = get_recipes_by_ingredient(keyword)
        elif selected_func == "suggest_menu_for_week":
            result = suggest_menu_for_week()
        elif selected_func == "quick_dishes_under_15_minutes":
            result = quick_dishes_under_15_minutes()
        else:
            result = "❌ Không tìm thấy hàm phù hợp."
    except Exception as e:
        result = f"❌ Có lỗi khi gọi hàm: {e}"

    print("\n📋 Kết quả:")
    if isinstance(result, str):
        print(result)
    else:
        for item in result:
            print(item)
