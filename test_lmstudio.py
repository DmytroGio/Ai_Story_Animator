from openai import OpenAI

# Указываем локальный сервер LM Studio
client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio"
)


def test_lmstudio_connection():
    """Проверка подключения к LM Studio"""
    try:
        completion = client.chat.completions.create(
            model="local-model",
            messages=[
                # Убираем system роль, используем только user и assistant
                {"role": "user", "content": "You are a helpful AI assistant. Say hello in one sentence."}
            ],
            temperature=0.7,
            max_tokens=100
        )

        response = completion.choices[0].message.content
        print("✅ LM Studio работает!")
        print(f"Ответ: {response}")
        return True

    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False


if __name__ == "__main__":
    test_lmstudio_connection()