from llama_index import GPTSimpleVectorIndex
from dotenv import load_dotenv
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import sys
import openai
import json
from create_index import create_index
openai.api_base = os.environ.get('OPENAI_PROXY')


app = Flask(__name__, static_folder="html")
CORS(app)

load_dotenv()


@app.route('/api/summarize', methods=["GET"])
def summarize_index():
    index_name = request.args.get("index")
    index = GPTSimpleVectorIndex.load_from_disk(
        f'./index/{index_name}.json')
    res = index.query(
        'summarize the article', response_mode="tree_summarize")

    return jsonify(res)


@app.route('/api/query', methods=["GET"])
def query_index():
    query_text = request.args.get("query")
    index_name = request.args.get("index")
    index = GPTSimpleVectorIndex.load_from_disk(
        f'./index/{index_name}.json')
    res = index.query(query_text)
    response_json = {
        "answer": str(res),
        "cost": index.llm_predictor.last_token_usage,
        "sources": [{"text": str(x.source_text),
                     "similarity": round(x.similarity, 2),
                     "extraInfo": x.extra_info
                     } for x in res.source_nodes]
    }
    return jsonify(response_json)


@app.route('/api/upload', methods=["POST"])
def upload_file():
    filepath = None
    try:
        uploaded_file = request.files["file"]
        filename = secure_filename(uploaded_file.filename)
        filepath = os.path.join('temp', os.path.basename(filename))
        uploaded_file.save(filepath)

        create_index(filepath, os.path.splitext(filename)[0])
    except Exception as e:
        # cleanup temp file
        print(e, 'upload error')
        if filepath is not None and os.path.exists(filepath):
            os.remove(filepath)
            return "Error: file exist", 500
        return "Error: {}".format(str(e)), 500

    # cleanup temp file
    if filepath is not None and os.path.exists(filepath):
        os.remove(filepath)

    return "File inserted!", 200


@app.route('/api/index-list', methods=["GET"])
def get_index_files():
    dir = "index"
    files = os.listdir(dir)
    return files


@app.route('/api/html-list', methods=["GET"])
def get_html_files():
    dir = "html"
    files = os.listdir(dir)
    return [{"path": f'/html/{file}', "name": os.path.splitext(file)[0]} for file in files]