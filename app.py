# app.py

from flask import Flask, request, jsonify, render_template
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)


DB_CONFIG = {
    'host': 'localhost',
    'user': 'root', 
    'password': 'jkk177374',
    'database': 'data1'
}

# --- 数据库连接函数 ---
def create_db_connection():
    """创建并返回一个数据库连接对象"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            print("成功连接到MySQL数据库")
    except Error as e:
        print(f"连接MySQL数据库失败: {e}")
    return connection

# --- 路由定义 ---

@app.route('/')
def login_page():
    """
    根路由，渲染登录页面。
    Flask会自动在 'templates' 文件夹中查找HTML文件。
    """
    return render_template('login.html')

@app.route('/register_page')
def register_page():
    """
    渲染注册页面。
    """
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    """
    处理员工注册请求。
    接收用户名、姓名、密码，并将其存储到数据库中。
    """
    data = request.get_json()
    username = data.get('username')
    name = data.get('name')
    password = data.get('password')

    if not all([username, name, password]):
        return jsonify({'message': '所有字段都不能为空！'}), 400

    connection = create_db_connection()
    if connection is None:
        return jsonify({'message': '数据库连接失败'}), 500

    cursor = connection.cursor()
    try:
        # 1. 检查用户名是否已存在
        cursor.execute("SELECT id FROM employee WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({'message': '用户名已存在，请选择其他用户名'}), 409 # 409 Conflict

        # 2. 插入新员工信息
        insert_query = "INSERT INTO employee (username, name, password) VALUES (%s, %s, %s)"
        cursor.execute(insert_query, (username, name, password))
        connection.commit() # 提交事务，保存更改
        return jsonify({'message': '注册成功！'}), 201 # 201 Created
    except Error as e:
        connection.rollback() # 发生错误时回滚事务
        print(f"注册失败: {e}")
        return jsonify({'message': f'注册失败: {e}'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL连接已关闭")

@app.route('/login', methods=['POST'])
def login():
    """
    处理员工登录请求。
    根据用户名、姓名、密码与数据库进行比对，返回登录结果。
    """
    data = request.get_json()
    username = data.get('username')
    name = data.get('name')
    password = data.get('password')

    if not all([username, name, password]):
        return jsonify({'message': '所有字段都不能为空！'}), 400

    connection = create_db_connection()
    if connection is None:
        return jsonify({'message': '数据库连接失败'}), 500

    cursor = connection.cursor(dictionary=True) # 使用 dictionary=True 可以按列名访问结果
    try:
        # 1. 首先根据姓名查找员工
        select_by_name_query = "SELECT username, name, password FROM employee WHERE name = %s"
        cursor.execute(select_by_name_query, (name,))
        employees_with_same_name = cursor.fetchall()

        if not employees_with_same_name:
            # 如果姓名不存在
            return jsonify({'message': '未找到该员工'}), 404 # 404 Not Found
        else:
            # 姓名存在，进一步比对用户名和密码
            found_exact_match = False
            for employee in employees_with_same_name:
                if employee['username'] == username and employee['password'] == password:
                    found_exact_match = True
                    break

            if found_exact_match:
                return jsonify({'message': '登录成功'}), 200 # 200 OK
            else:
                # 姓名正确，但用户名或密码不匹配
                return jsonify({'message': '用户名或密码错误'}), 401 # 401 Unauthorized

    except Error as e:
        print(f"登录失败: {e}")
        return jsonify({'message': f'登录失败: {e}'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL连接已关闭")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
