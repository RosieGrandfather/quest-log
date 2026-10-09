"""sql-0 共用：导入 unitlib / runlib，提供答案位置调整、统一的练习数据库建表代码和参考资料"""
from unitlib import *
from runlib import Notebook

def retarget(unit, target):
    for q, t in zip(unit["quiz"]["questions"], target):
        q["options"][q["answer"]], q["options"][t] = q["options"][t], q["options"][q["answer"]]
        q["answer"] = t

# 每一节开头都要重新建库（网页里每进入一节都会清空变量）。数据是自己编的演示数据，不是任何真实系统的数据
SETUP_DATA = '''
# 练习数据库：客户、产品、订单、订单明细、库存（自己编的演示数据）
import sqlite3
db = sqlite3.connect(":memory:")
db.executescript("""
CREATE TABLE customers(cust_id INTEGER PRIMARY KEY, name TEXT, country TEXT);
CREATE TABLE products(sku TEXT PRIMARY KEY, name TEXT, category TEXT, unit_cost REAL);
CREATE TABLE orders(order_id INTEGER PRIMARY KEY, cust_id INTEGER, order_date TEXT, status TEXT);
CREATE TABLE order_lines(order_id INTEGER, line_no INTEGER, sku TEXT, qty INTEGER, unit_price REAL);
CREATE TABLE inventory(sku TEXT, warehouse TEXT, on_hand INTEGER, stock_status TEXT);
""")
ins = lambda t, rows: db.executemany(f"INSERT INTO {t} VALUES ({','.join('?'*len(rows[0]))})", rows)
ins("customers", [(1,"Alpha Pharmacy","SG"),(2,"Beta Clinic","SG"),(3,"Gamma Trading","MY"),
                  (4,"Delta Retail","MY"),(5,"Echo Health","SG"),(6,"Foxtrot Store",None)])
ins("products", [("BP100","Arm BP Monitor","BP",30.0),("BP200","Wrist BP Monitor","BP",22.0),
                 ("TH10","Thermometer","TEMP",4.0),("NB50","Nebulizer","NEB",35.0),
                 ("MS01","Massager","PAIN",18.0),("OLD9","Old Model","BP",10.0)])
ins("orders", [(101,1,"2026-09-01","SHIPPED"),(102,1,"2026-09-03","SHIPPED"),(103,2,"2026-09-03","OPEN"),
               (104,3,"2026-09-05","SHIPPED"),(105,3,"2026-09-12","CANCELLED"),(106,4,"2026-09-15","OPEN"),
               (107,5,"2026-09-20","SHIPPED"),(108,2,"2026-09-22","SHIPPED"),(109,9,"2026-09-25","OPEN")])
ins("order_lines", [(101,1,"BP100",10,55.0),(101,2,"TH10",50,9.0),(102,1,"BP200",20,40.0),
                    (103,1,"NB50",5,70.0),(104,1,"BP100",8,56.0),(104,2,"MS01",10,35.0),
                    (105,1,"TH10",100,9.0),(106,1,"BP200",15,41.0),(106,2,"TH10",30,9.5),
                    (107,1,"NB50",10,69.0),(107,2,"BP100",12,55.0),(108,1,"MS01",6,36.0),
                    (108,2,"XX99",2,10.0),(109,1,"BP100",4,55.0)])
ins("inventory", [("BP100","SG-WH",120,"AVAIL"),("BP100","SG-WH",30,"QUAR"),("BP200","SG-WH",200,"AVAIL"),
                  ("TH10","SG-WH",500,"AVAIL"),("NB50","MY-WH",40,"AVAIL"),("MS01","MY-WH",0,"AVAIL"),
                  ("BP200","MY-WH",25,"QUAR"),("OLD9","SG-WH",15,"AVAIL")])
db.commit()    # 先把建好的数据提交，后面的 rollback 才不会把它也撤销
print("建库完成：5 张表")
'''
SETUP_Q = '''
# 辅助函数 q(sql)：运行一条 SQL 并打印结果表
def q(sql, params=()):
    cur = db.execute(sql, params)
    rows = cur.fetchall()
    if cur.description:
        print(" | ".join(d[0] for d in cur.description))
        for r in rows:
            print(" | ".join("NULL" if v is None else str(v) for v in r))
        print(f"({len(rows)} 行)")
'''
SQLITE_DOC = {"title": "SQLite 官方文档：SQL 语法与窗口函数", "url": "https://www.sqlite.org/lang.html", "note": "本课程练习用的 SQLite 的语法说明；Oracle 的写法在第 8 节单独对照"}
ORACLE_SQL_REF = {"title": "Oracle 官方文档：Database SQL Language Reference", "url": "https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/", "note": "Oracle 方言以这份官方文档为准（19c 版本）"}
