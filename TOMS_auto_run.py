import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd

# Create GUI Window
root = tk.Tk()
root.title("非补处理工具")
root.geometry("1000x400")

file_labels = [    
    "1. 选择 delivery_list.csv",
    "2. 选择 sdb_sap_replenish_sales_orders.csv",
    "3. 选择 sdb_sap_replenish_sales_orders_gift.csv",
    "4. 选择 补销售错误单据导出.csv",
    "5. 选择 SAP补销售.csv",
    "6. 选择 SAP特价.csv"
]

file_paths = [tk.StringVar() for _ in range(6)]

def browse_file(index):
    path = filedialog.askopenfilename(title=file_labels[index])
    if path:
        file_paths[index].set(path)

# GUI layout for file selectors
for i, label in enumerate(file_labels):
    tk.Label(root, text=label, anchor="w").grid(row=i, column=0, padx=10, pady=8, sticky="w")
    tk.Entry(root, textvariable=file_paths[i], width=70).grid(row=i, column=1, padx=10, pady=8)
    tk.Button(root, text="浏览", command=lambda i=i: browse_file(i)).grid(row=i, column=2, padx=5)

# Main processing logic
def run_program():
    try:
        paths = [fp.get() for fp in file_paths]
        if not all(paths):
            messagebox.showerror("错误", "请先选择所有6个文件。")
            return

        # Load all files
        df = pd.read_csv(paths[0])
        df_main = pd.read_csv(paths[1])
        df_gift = pd.read_csv(paths[2])
        df_error_msg = pd.read_csv(paths[3], encoding='gbk')
        df_SAP_Resale = pd.read_csv(paths[4], encoding='gbk', low_memory=False)
        df_SAP_Special_Resale = pd.read_csv(paths[5], encoding='gbk', low_memory=False)

        # Begin data processing
        # 1. 根据订单号填充“是否需要补销售”列表 （Q列）
        # 平台自发货，全部为是
        # 非平台自发货（包括空白）：”是否401或者601“是，且发货时间不为空，填入是
        df['是否需要补销售'] = 0  # or any constant like "N/A"
        df['是否需要补销售'] = df['订单类型'].apply(lambda x: '是' if x == '平台发货' else '0')
        cond2 = (df['订单类型'] != '平台发货') & \
                (df['是否401或601'] == '是') & \
                (df['发货时间'].notna())
        df.loc[cond2, '是否需要补销售'] = '是'
        df.loc[df['是否需要补销售']=='0', '是否需要补销售'] = '否'
        # 2. 根据订单号填充“补销售推送平台”和“补销售单号”列表
        df_gift['汇总单号'] = '零元补销售'
        df_gift['推送平台'] = '零元补销售'
        df_all = pd.concat([df_main, df_gift], ignore_index=True)
        df_lookup = df_all[['delivery_item_id', '推送平台', '汇总单号']]
        df_lookup.rename(columns={
            'delivery_item_id': '发货单商品明细ID',
        }, inplace=True)
        df = df.merge(df_lookup, on='发货单商品明细ID', how='left')
        df_error_msg = df_error_msg[['订单号(order_bn)','错误信息(msg)']]
        df_error_msg['订单号(order_bn)'] = df_error_msg['订单号(order_bn)'].str.replace("'", "", regex=False)
        df_error_msg.rename(columns={
            '订单号(order_bn)': '订单号',
            '错误信息(msg)':'补销售失败原因',
        }, inplace=True)
        df['订单号'] = df['订单号'].str.replace("'", "", regex=False)
        df_temp = df.merge(df_error_msg, on='订单号', how='left')
        condition = (df['是否需要补销售'] == '是') & (df['推送平台'].isna())
        df.loc[condition, '补销售失败原因'] = df_temp.loc[condition, '补销售失败原因']
        # 填充“SAP销售单号”，“SAP创建时间（选择的时候去掉为空的销售单号）”，和“SAP关闭时间（选择的时候去掉为空的销售单号）”
        df_SAP_Resale = df_SAP_Resale[['补销售单号','SAP销售单号','SAP创建日期','SAP关闭日期']]
        df_SAP_Resale.rename(columns={
            '补销售单号': '汇总单号',
        }, inplace=True)
        df_temp = df.merge(df_SAP_Resale, on='汇总单号', how='left')
        condition_Sap = (df['推送平台'] == 'SAP')
        df.loc[condition_Sap, ['SAP销售单号','SAP创建日期','SAP关闭日期']] = df_temp.loc[condition_Sap, ['SAP销售单号','SAP创建日期','SAP关闭日期']]
        # 填充“特价SAP销售单号”，“特价SAP创建时间（选择的时候去掉为空的销售单号）”和“特价SAP关闭时间（选择的时候去掉为空的销售单号）
        df_SAP_Special_Resale = df_SAP_Special_Resale[['补销售单号','SAP销售单号','SAP创建日期','SAP关闭日期']]
        df_SAP_Special_Resale.rename(columns={
            '补销售单号': '汇总单号',
            'SAP销售单号': '特价SAP销售单号',
            'SAP创建日期': '特价SAP创建日期',
            'SAP关闭日期': '特价SAP关闭日期',
        }, inplace=True)
        df_temp = df.merge(df_SAP_Special_Resale, on='汇总单号', how = 'left')
        condition_Special_Sap = (df['推送平台'] == '决裁')
        df.loc[condition_Special_Sap, ['特价SAP销售单号','特价SAP创建日期','特价SAP关闭日期']] \
        = df_temp.loc[condition_Special_Sap, ['特价SAP销售单号','特价SAP创建日期','特价SAP关闭日期']]
        df = df[df['是否经销商店铺'] == '否']
        condition = df['发货时间'].isna() & (df['订单状态'] == '活动订单') 
        df.loc[condition, '订单状态'] = '未完成'
        df.loc[(df['发货单状态'] == '待处理'), '发货单状态'] = '未发货'
        # 发货单号+’
        df['发货单号'] = df['发货单号'].apply(lambda x: f"'{x}")
        # Save result
        output_path = filedialog.asksaveasfilename(
            title="保存 Excel 文件",
            defaultextension=".xlsx",
            filetypes=[("Excel 文件", "*.xlsx")]
        )
        if output_path:
            df.to_excel(output_path, index=False)
            messagebox.showinfo("成功", f"文件已保存：\n{output_path}")
        else:
            messagebox.showwarning("取消", "未保存任何文件。")

    except Exception as e:
        messagebox.showerror("发生错误", str(e))

# Run Button
run_btn = tk.Button(root, text="运行程序", command=run_program, bg="green", fg="white", width=15)
run_btn.grid(row=6, column=2, pady=30, sticky='e')

# Start GUI
root.mainloop()
