from django.shortcuts import render
from tensorflow.keras.models import load_model
import numpy as np
import re
from django.shortcuts import render
from django.core.paginator import Paginator
from datetime import datetime
import os

 # Hàm xử lý Dashboard và đọc file log
def dashboard_view(request):
    log_entries = []

    # Đọc file log và xử lý từng dòng
    log_file_path = os.path.join(os.path.dirname(__file__), 'file', 'web_server.log')
    with open(log_file_path, 'r') as file:
        for line in file:
            # Bỏ qua dòng tiêu đề hoặc các dòng không phải log
            if line.startswith("#") or not line.strip():
                continue
            
            # Định dạng log mới: `timestamp, source_ip, dest_ip, src_port, dst_port, other_info`
            match = re.match(r'(\S+ \S+), (\S+), (\S+), (\d+), (\d+), (.*)', line)
            if match:
                timestamp, source_ip, dest_ip, src_port, dst_port, other_info = match.groups()
                
                # Định dạng lại thời gian
                log_date = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                formatted_date = log_date.strftime("%H:%M:%S %d-%m-%Y")

                # Thêm mục log đã xử lý vào danh sách
                log_entries.append({
                    'date': formatted_date,
                    'source_ip': source_ip,
                    'dest_ip': dest_ip,
                    'source_port': src_port,
                    'dest_port': dst_port,
                    'info': other_info  
                })

    # Tìm kiếm theo từ khóa
    query = request.GET.get('q')
    if query:
        log_entries = [
		entry for entry in log_entries 
		if query in entry['date'] or 
		   query in entry['source_ip'] or 
		   query in entry['dest_ip'] or 
		   query in entry['source_port'] or 
		   query in entry['dest_port'] or 
		   query in entry['info']
    	]

    # Phân trang - mỗi trang hiển thị 20 dòng
    paginator = Paginator(log_entries, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'dashboard.html', {'page_obj': page_obj, 'query': query})
    
def model_view(request):
    result = None
    if request.method == 'POST':
        url_input = request.POST.get('input_data')
        
        # Tiền xử lý URL (ví dụ: loại bỏ ký tự đặc biệt, rút trích thông tin cần thiết)
        processed_input = preprocess_url(url_input)
        
        # Tải model và thực hiện dự đoán
        model_file_path = os.path.join(os.path.dirname(__file__), 'file', 'model.h5')
        model = load_model(model_file_path)
        input_array = np.array([processed_input])  # Chuyển thành numpy array

        result = model.predict(input_array)[0][0]  # Dự đoán và lấy kết quả
    return render(request, 'model.html', {'result': result})

# Hàm tiền xử lý URL
def preprocess_url(url):
    # Xóa ký tự không cần thiết và chuyển về chữ thường
    url = url.lower()
    url = re.sub(r'[^a-zA-Z0-9]', ' ', url)  # Loại bỏ ký tự đặc biệt
    
    # Biểu diễn ký tự dưới dạng mã ASCII
    url_vector = np.array([ord(char) for char in url])
    
    # Đảm bảo đầu ra có chiều dài 1000
    if len(url_vector) < 1000:
        # Thêm padding
        url_vector = np.pad(url_vector, (0, 1000 - len(url_vector)), 'constant')
    elif len(url_vector) > 1000:
        # Cắt bớt nếu quá dài
        url_vector = url_vector[:1000]
        
    return url_vector

