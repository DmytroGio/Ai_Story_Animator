from openai import OpenAI

# Specify local LM Studio server
client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio"
)


def test_lmstudio_connection():
    """Check connection to LM Studio"""
    try:
        completion = client.chat.completions.create(
            model="local-model",
            messages=[
                # Remove system role, use only user and assistant
                {"role": "user", "content": "You are a helpful AI assistant. Say hello in one sentence."}
            ],
            temperature=0.7,
            max_tokens=100
        )

        response = completion.choices[0].message.content
        print("✅ LM Studio is working!")
        print(f"Response: {response}")
        return True

    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False


if __name__ == "__main__":
    test_lmstudio_connection()
