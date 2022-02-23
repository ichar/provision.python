#!/usr/bin/python3
# -*- coding: utf-8 -*-

import pymssql
pymssql.__version__

#import pyodbc as db

import sqlalchemy
sqlalchemy.__version__

default_print_encoding = 'cp866'
default_unicode        = 'utf-8'
default_encoding       = 'cp1251'
default_iso            = 'ISO-8859-1'

from sqlalchemy import create_engine
#connection = { 'server':'localhost', 'user':'sa', 'password':'admin', 'database':'BankDB' }
#connection = { 'server':'LAPTOP-WORK', 'user':'sa', 'password':'admin', 'database':'BankDB' }
connection = { 'server':'192.168.0.62', 'user':'sa', 'password':'admin', 'database':'BankDB', 'encoding':default_encoding }
engine = create_engine('mssql+pymssql://%(user)s:%(password)s@%(server)s' % connection)
#engine = create_engine('mssql+pyodbc://localhost/ProvisionDB?trusted_connection=yes&driver=SQL+Server')

def printData(cursor):
    rows = []
    encoding = connection.get('encoding') or default_iso
    for n, row in enumerate(cursor):
        if n > 100:
            break
        rows.append(row)
        print('-->', n, row[0], row[1].encode(encoding).decode(default_encoding))
    len(rows)

def run():
    sql = 'SELECT TOP 100 TID,Article,Total FROM [ProvisionDB].[dbo].[Orders_tb] order by TID desc'
    cursor = engine.execute(sql)
    printData(cursor)

def execute():
    #conn = db.connect('server=localhost;database=ProvisionDB;trusted_connection=yes;driver={SQL Server}')
    
    sql = "EXEC [ProvisionDB].[dbo].[REGISTER_Order_sp] 0,'sales','Чип   KONA 2 D2320 6pin silver (Visa, MC)',1000000,'Под сток',0.30500,'USD',305000.00,50833.33,'ОДК','срочная','заявка Н. Коблысь (сток от Коны)','KONA I CO||||Seoul, 8F Floor EXCON Venture-Tower 3, Eunhaeng-ro, Yeongdeungpo-gu||000003560||','постоплата 90 дней','','','2019-11-19','polina',-1,0,0,null"
    #sql = "EXEC [ProvisionDB].[dbo].[REGISTER_Order_sp] @p_Mode=0,@p_Login='sales',@p_Article='Чип   KONA 2 D2320 6pin silver (Visa, MC)',@p_Qty=1000000,@p_Purpose='Под сток',@p_Price=0.30500,@p_Currency='USD',@p_Total=305000.00,@p_Tax=50833.33,@p_Subdivision='ОДК',@p_Category='срочная',@p_Equipment='заявка Н. Коблысь (сток от Коны)',@p_Seller='KONA I CO||||Seoul, 8F Floor EXCON Venture-Tower 3, Eunhaeng-ro, Yeongdeungpo-gu||000003560||',@p_Condition='постоплата 90 дней',@p_Account='',@p_URL='',@p_DueDate='2019-11-19',@p_EditedBy='polina',@p_Status=-1,@p_IsNoPrice=0,@p_RowSpan=0,@p_Output=null"
    #sql = "{CALL [ProvisionDB].[dbo].[REGISTER_Order_sp](@p_Mode=0,@p_Login='sales',@p_Article='Чип   KONA 2 D2320 6pin silver (Visa, MC)',@p_Qty=1000000,@p_Purpose='Под сток',@p_Price=0.30500,@p_Currency='USD',@p_Total=305000.00,@p_Tax=50833.33,@p_Subdivision='ОДК',@p_Category='срочная',@p_Equipment='заявка Н. Коблысь (сток от Коны)',@p_Seller='KONA I CO||||Seoul, 8F Floor EXCON Venture-Tower 3, Eunhaeng-ro, Yeongdeungpo-gu||000003560||',@p_Condition='постоплата 90 дней',@p_Account='',@p_URL='',@p_DueDate='2019-11-19',@p_EditedBy='polina',@p_Status=-1,@p_IsNoPrice=0,@p_RowSpan=0,@p_Output=null)}"
    #sql = "{CALL [ProvisionDB].[dbo].[REGISTER_Order_sp](@p_Mode=?,@p_Login=?,@p_Article=?,@p_Qty=?,@p_Purpose=?,@p_Price=?,@p_Currency=?,@p_Total=?,@p_Tax=?,@p_Subdivision=?,@p_Category=?,@p_Equipment=?,@p_Seller=?,@p_Condition=?,@p_Account=?,@p_URL=?,@p_DueDate=?,@p_EditedBy=?,@p_Status=?1,@p_IsNoPrice=?,@p_RowSpan=?,@p_Output=?)}"
    #sql = "{CALL [ProvisionDB].[dbo].[REGISTER_Order_sp](?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)}"
    #sql = "EXEC [ProvisionDB].[dbo].[REGISTER_Order_sp] ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?"
    #sql = "DECLARE @p_Output varchar(20); EXEC [ProvisionDB].[dbo].[REGISTER_Order_sp] ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,@p_Output; SELECT @p_Output AS the_output;"
    params = (0,'sales','Чип   KONA 2 D2320 6pin silver (Visa, MC)',1000000,'Под сток',0.30500,'USD',305000.00,50833.33,'ОДК','срочная','заявка Н. Коблысь (сток от Коны)','KONA I CO||||Seoul, 8F Floor EXCON Venture-Tower 3, Eunhaeng-ro, Yeongdeungpo-gu||000003560||','постоплата 90 дней','','','2019-11-19','polina',-1,0,0,None)

    conn = engine.connect()
    #conn = engine.raw_connection()

    with conn.begin() as trans:
        try:
            #cursor = conn.cursor()
            #print(0)
            #cursor.execute(sql, params)
            #cursor = conn.execute(sql, params)
            cursor = conn.execute(sql)
            print(1)
            rows = cursor.fetchall()
            print(2)
            printData(rows)
            trans.commit()
            #conn.commit()
            print(3)
        except Exception as ex:
            trans.rollback()
            #conn.close()
            print(ex)
        
#execute()
run()
