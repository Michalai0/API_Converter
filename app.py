from flask import Flask, request, jsonify, Response, stream_with_context
import requests
import json
from flask_cors import CORS
import re


app = Flask(__name__)
CORS(app)
API_BASE_URL = "https://api.m513.cc/v1/chat/completions"  # 替换为实际的API基础URL
# 定义常见图片格式的正则表达式
image_pattern = re.compile(r'.*\.(jpg|jpeg|png|gif|bmp|tiff|svg)$', re.IGNORECASE)
timeout_duration = 600
claude_model = ['claude-3.5-sonnet', 'claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307']
def json_to_python_boolean(value):
    if isinstance(value, bool):
        return value
    elif isinstance(value, str):
        return value.lower() == 'true'
    else:
        return False


def convert_messages(messages, model):
    converted_messages = []
    for message in messages:
        role = message.get("role")
        content = message.get("content")
        if role and isinstance(content, list):
            if model in claude_model:
                model = model + '-vision'
            converted_messages.append({
                "role": role,
                "content": content
            })
        elif role and isinstance(content, str) and (content.startswith("https://michalai-ai.oss-cn-hongkong.aliyuncs.com") or content.startswith("https://cdn.m513.cc")):
            lines = content.split("\n\n")
            if model == "gpt-4-all" or model == "gpt-4o-all" or model == "gpt-4o-mini-all":
                print("OpenAI")
                print(model)
                converted_content = []
                for line in lines:
                    if line.strip().startswith(
                            ("https://michalai-ai.oss-cn-hongkong.aliyuncs.com", "https://cdn.m513.cc")):
                        converted_content.append({
                            "type": "file",
                            "file_url": {
                                "url": line.strip()
                            }
                        })
                    elif line.strip():  # This will capture non-empty lines that are not URLs
                        converted_content.append({
                            "type": "text",
                            "text": line.strip()
                        })

                converted_messages.append({
                    "role": role,
                    "content": converted_content
                })
            else:
                if model in claude_model:
                    model = model + '-vision'
                converted_content = []
                for line in lines:
                    if image_pattern.search(line):
                        converted_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": line.strip()
                            }
                        })
                    elif line.strip().startswith(("https://michalai-ai.oss-cn-hongkong.aliyuncs.com", "https://cdn.m513.cc")):
                        converted_content.append({
                            "type": "file",
                            "file_url": {
                                "url": line.strip()
                            }
                        })
                    elif line.strip():
                        converted_content.append({
                            "type": "text",
                            "text": line.strip()
                        })

                converted_messages.append({
                    "role": role,
                    "content": converted_content
                })

        else:
            converted_messages.append(message)

    return converted_messages, model


def streaming(converted_data, headers, stream_p):
    response = requests.post(API_BASE_URL, json=converted_data, headers=headers, stream=stream_p, timeout=timeout_duration)
    if response.status_code == 200:
        for line in response.iter_lines():
            if line:
                print(line)
                data = line.decode('utf-8')
                yield f"{data}\n\n"
    else:
        error = response.text
        yield json.dumps({'error': f'{error}Failed to push converted data to API'}).encode('utf-8')


@app.route('/')
def stream():
    return 'ok'


@app.route("/v1/chat/completions", methods=["POST"])
def convert_api():
    data = request.get_json()

    if data:
        model = data.get("model")
        messages = data.get("messages")
        is_stream = data.get("stream", True)

        print("更改前的JSON文件:")
        print(json.dumps(data, indent=2))

        if model and messages:
            converted_messages, model = convert_messages(messages, model)
            print(model)
            converted_data = {
                "model": model,
                "messages": converted_messages,
                "stream": is_stream
            }

            print("更改后的JSON文件:")
            print(json.dumps(converted_data, indent=2, ensure_ascii=False))
            stream_p = json_to_python_boolean(is_stream)

            # 获取原始请求的headers
            headers = dict(request.headers)
            return Response(stream_with_context(streaming(converted_data, headers, stream_p)), mimetype='text/event-stream')

        return jsonify({"error": "Invalid request data"}), 400
    else:
        return jsonify({"error": "No request data"}), 400


if __name__ == "__main__":
    app.run(debug=True, port=50601, host='0.0.0.0')