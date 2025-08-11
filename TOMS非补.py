import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd

# Create GUI Window
root = tk.Tk()
root.title("非补处理工具")
root.geometry("1000x200")

file_labels = [
    "1. 选择 delivery_list_不补销售.csv"
]

file_paths = [tk.StringVar() for _ in range(1)]

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

        # Begin data processing
        df.loc[df['发货单状态'] == '待处理', '发货单状态'] = '未发货'
        df.loc[df['发货单状态'] == '打回', '发货单状态'] = '已取消'
        df.loc[(df['订单状态'] == '活动订单') & (df['发货时间'].isnull()), '订单状态'] = '未完成'

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
