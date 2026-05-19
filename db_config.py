# 数据库配置
DB_CONFIG = {
    "host": "10.11.150.253",
    "port": 3306,
    "database": "ry-vue-py",
    "user": "root",
    "password": "Qwe123!!"
}

# 表名
TABLE_NAME = "ai_interview_resume"

# 静态查询条件
STATIC_CONDITIONS = {
    "visible": 1,
    "interview_status": 0
}

# end_time 字段名（用于动态日期比较：end_time > 今天）
END_TIME_FIELD = "end_time"

# 基础 URL
BASE_URL = "https://10.11.150.127:8667/h5-digitalHuman?token="
