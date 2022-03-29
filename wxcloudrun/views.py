from datetime import datetime
from flask import render_template, request
from run import app
from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid
from wxcloudrun.model import Counters
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response

import zipfile
import plistlib
import subprocess
import json
import datetime
import sys,os,re
import io

#首页
@app.route("/", methods=["GET", "POST"])
def index():
    """
    :return: 返回index页面
    """
    print("request.args:"+str(request.args))
    (plist_info,mobileprovision_info)=(None,None)
    return render_template('index.html',data=plist_info)



# 解压ipa获取并信息
def unzip_ipa(file):
    ipa_file = zipfile.ZipFile(file)    
    plist_path = find_path(ipa_file, 'Payload/[^/]*.app/Info.plist')
    # 读取plist内容
    plist_data = ipa_file.read(plist_path)
    # 解析plist内容
    plist_info = plistlib.loads(plist_data)
    
    # 获取mobileprovision文件路径
    provision_path = find_path(ipa_file, 'Payload/[^/]*.app/embedded.mobileprovision')
    provision_data = ipa_file.read(provision_path)
    mobileprovision_info=get_mobileprovision(provision_data)
    file.seek(0, os.SEEK_END)
    size = file.tell()
    zip_M = float(size) / float(1000*1000)  # MB
    plist_info["filesize"]=str(format(zip_M,'.2f'))
    return (plist_info,mobileprovision_info)


def get_mobileprovision(content):
        provision_xml_rx = re.compile(br'<\?xml.+</plist>', re.DOTALL)
        match = provision_xml_rx.search(content)
        if match:
            xml_content = match.group()
            data = plistlib.loads(xml_content)
            #移除无用信息（影响阅读~）          
            data.setdefault("DeveloperCertificates","")
            data.setdefault("DER-Encoded-Profile","")
            del data["DeveloperCertificates"]
            del data["DER-Encoded-Profile"]
            return data
        else:
            return None 
    
# 获取plist路径
def find_path(zip_file, pattern_str):
    name_list = zip_file.namelist()
    pattern = re.compile(pattern_str)
    for path in name_list:
        m = pattern.match(path)
        if m is not None:
            return m.group()
        


@app.route("/upload_file", methods=["GET", "POST"])
def upload_file():
    print("upload_fileAction")
    plist_info={};
    if request.files:
        print(request.files)
        print("======request.files========")
        file = request.files['file']
        print(file)
        if file:
            filename = file.filename
            file_like_object=io.BytesIO(file.read())
            unzip_ipa(file)
            (plist_info,mobileprovision_info)=unzip_ipa(file_like_object)
            print(plist_info)
            return json.dumps(plist_info)
    else:
        return json.dumps(plist_info)
    