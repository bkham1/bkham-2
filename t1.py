from asyncio import run, sleep, gather
from typing import Dict, Any, List, Union
from aminodorksfix.asyncfix import (
    Client,
    SubClient
)
import random

# --- ⚙️ الإعدادات الأساسية ---
API_KEY = "1bd49e6563fb5b744a999b6c050197a9"
EMAIL = "abosaeg8@gmail.com"
PASSWORD = "foo40k"
TARGET_COMMUNITY_LINK = "http://aminoapps.com/c/anime-empire-1"

# --- 💬 إعدادات العشوائية والتكرار ---
RANDOM_COMMENTS = [
    "هههههه", "يرجال", "هففف", "اها", "شايفك", 
    "امااا", "...", "جاري التفكير", "غريب", "وش ذا",
    "قوي!", "طيب", "بفكر", "ممتاز", "واو"
]
MAX_INTERACTION_RETRIES = 3 
LAST_KNOWN_POST_ID = None

# --- 🎨 تنسيق المخرجات ---
def colorize(text: str, status: str) -> str:
    return f"\033[94m[\033[0m{status}\033[94m] \033[0m{text}\033[94m"

# --- 🔒 وظائف الدخول ---
async def login(client: Client) -> None:
    if not all([API_KEY, EMAIL, PASSWORD]):
        raise ValueError("Missing Credentials")
    try:
        print(colorize("جارٍ محاولة تسجيل الدخول...", "*"))
        await client.login(EMAIL, PASSWORD)
        print(colorize("تم تسجيل الدخول بنجاح! 🚀", "+"))
    except Exception as e:
        print(f"\033[0;31m[LoginError]: فشل تسجيل الدخول: {e}\033[0m")
        raise e

# --- ❤️‍🔥 وظيفة التفاعل الأساسية (لايك + تعليق عشوائي) ---
async def interact_with_post(sub_client: SubClient, primary_id: str, post_type: str, post_data: Dict[str, Any], max_retries: int = MAX_INTERACTION_RETRIES) -> None:
    
    comment_text = random.choice(RANDOM_COMMENTS)
    
    # تحديد المعرفات البديلة لضمان التفاعل مع كل أنواع المنشورات
    blog_id = post_data.get("blogId") # للمدونات والمنشورات العادية
    object_id = post_data.get("objectId") or post_data.get("blogId") # للـ Wikis والـ Quizzes، نعتمد على blogId كبديل

    # وظيفة محاولة التفاعل الفعلية
    async def attempt_interaction_logic(current_attempt: int):
        
        # 1. الإعجاب (يعمل على كل أنواع المنشورات بدون استثناء)
        if post_data.get("type") in [2, 3]: # 2=Wiki, 3=Quiz
            await sub_client.like_wiki(objectId=object_id)
        else: # 1, 4, 5, 6, 7, 8, 9 (مدونة، سؤال، رابط، صورة، إلخ)
            await sub_client.like_blog(blogId=blog_id)
            
        print(colorize(f"تم وضع إعجاب (المحاولة {current_attempt}) على {post_type} بمعرّف: {primary_id}", "👍"))
        
        # 2. التعليق (نستخدم المعرّف الأكثر احتمالية للنجاح)
        await sub_client.comment(
            message=comment_text,
            blogId=blog_id if blog_id else object_id 
        )
        print(colorize(f"تم وضع تعليق (المحاولة {current_attempt}) على {post_type} بمعرّف: {primary_id}: '{comment_text}' ", "💬"))
        return True

    for attempt in range(max_retries):
        try:
            await attempt_interaction_logic(attempt + 1)
            return 
        
        except Exception as e:
            error_msg = str(e)
            
            # معالجة الأخطاء الآمنة للخروج
            if "has already been liked" in error_msg or "Comment has already been created" in error_msg:
                print(colorize(f"تم الإعجاب أو التعليق على {primary_id} مسبقاً في وقت قصير. تم التخطي.", "-"))
                return

            # تسجيل الخطأ بوضوح والمحاولة مرة أخرى
            print(f"\033[0;33m[Retry]: فشل التفاعل مع {primary_id} في المحاولة {attempt + 1}/{max_retries}: {error_msg}\033[0m")
            await sleep(1)

    print(f"\033[0;31m[Skip-Failed]: فشل التفاعل النهائي مع المنشور {primary_id} بعد {max_retries} محاولات. تم التخطي.\033[0m")

# --- 🔄 وظيفة المراقبة الرئيسية ---
async def monitor_community(sub_client: SubClient, target_com_id: str) -> None:
    global LAST_KNOWN_POST_ID

    while True:
        print("\n" + colorize("جاري فحص أحدث 5 منشورات...", "*"))

        try:
            blogs_response = await sub_client.get_recent_blogs(start=0, size=5) 
            response_json: Union[Dict[str, Any], List[Dict[str, Any]]] = blogs_response.json
            
            posts: List[Dict[str, Any]] = response_json.get("blogList", []) if isinstance(response_json, dict) else (response_json if isinstance(response_json, list) else [])
            
            if not posts:
                 print(colorize("لم يتم العثور على أي منشورات حديثة.", "-"))
                 await sleep(5)
                 continue

            current_latest_post_id = posts[0].get("blogId") or posts[0].get("objectId")

            if LAST_KNOWN_POST_ID is None:
                LAST_KNOWN_POST_ID = current_latest_post_id
                print(colorize(f"تم تسجيل المعرّف الأولي {LAST_KNOWN_POST_ID}. بدء المراقبة للجديد الذي يليه...", "✓"))
            
            elif current_latest_post_id != LAST_KNOWN_POST_ID:
                
                new_posts_tasks = []
                
                for post in posts:
                    # نعتمد على blogId أو objectId كـ ID أساسي للمقارنة
                    post_id = post.get("blogId") or post.get("objectId")
                    
                    if post_id == LAST_KNOWN_POST_ID:
                        break
                        
                    post_type = "Wiki" if post.get("type") == 2 else "Blog/Post" 
                    
                    print(colorize(f"تم العثور على منشور جديد للتفاعل: {post_id}", "🆕"))
                    
                    # نمرر المنشور كاملاً لتمكين دالة التفاعل من تحديد المعرّفات اللازمة
                    new_posts_tasks.append(
                        interact_with_post(sub_client, post_id, post_type, post) 
                    )
                
                LAST_KNOWN_POST_ID = current_latest_post_id
                
                if new_posts_tasks:
                    print(colorize(f"تم العثور على {len(new_posts_tasks)} منشور جديد. جاري التفاعل بالتوازي وبسرعة...", "⚡"))
                    await gather(*new_posts_tasks)
                else:
                    print(colorize("المنشورات الجديدة تم معالجتها سابقاً أو لا يوجد جديد.", "-"))

            else:
                print(colorize("لم يتم العثور على منشور جديد. المنشور الأحدث لم يتغير. 😴", "-"))

        except Exception as e:
            print(f"\033[0;31m[MonitorError]: خطأ أثناء جلب أو معالجة المنشورات: {e}\033[0m")
        
        print(colorize("الانتظار لمدة 5 ثوانٍ قبل الفحص التالي...", "⏳"))
        await sleep(5)

# --- 🏁 الدالة الرئيسية للتشغيل ---
async def main():
    client = Client(api_key=API_KEY, socket_enabled=False)

    try:
        await login(client)
    except Exception:
        return

    print(colorize("جاري تحليل رابط المجتمع للحصول على المعرّف...", "*"))
    try:
        link_data = await client.get_from_code(TARGET_COMMUNITY_LINK)
        target_com_id = getattr(link_data, 'comId', None)

        if not target_com_id:    
            print(f"\033[0;31m[FATAL ERROR]: لم يتم العثور على معرّف مجتمع (ComId).")    
            return

    except Exception as e:
        print(f"\033[0;31m[FATAL ERROR]: فشل في تحليل الرابط: {e}\033[0m")
        return

    sub_client = SubClient(comId=target_com_id, profile=client.profile)

    print(colorize(f"بدء بوت المراقبة للمجتمع: {target_com_id}", "✅"))
    await monitor_community(sub_client, target_com_id)

if __name__ == "__main__":
    try:
        run(main())
    except Exception as e:
        print(f"\033[0;31m[TERMINATED]: تم إيقاف البوت بسبب خطأ حاسم: {e}\033[0m")
