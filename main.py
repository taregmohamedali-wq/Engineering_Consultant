import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import fitz, docx, pandas as pd
import os, threading
import g4f

class FullComparisonApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI Engineering Consultant - Deep Technical Analysis")
        self.geometry("1300x900")
        self.lang = "AR"
        self.file1_path = ""
        self.file2_path = ""
        self.final_data = []
        self.setup_ui()

    def setup_ui(self):
        for widget in self.winfo_children(): widget.destroy()
        
        # Header
        self.btn_lang = ctk.CTkButton(self, text="English" if self.lang=="AR" else "العربية", command=self.toggle_lang)
        self.btn_lang.pack(pady=10, padx=20, anchor="ne")
        
        title_text = "المستشار الهندسي - تحليل المواصفات والعروض العميق" if self.lang=="AR" else "AI Engineering - Deep Analysis"
        ctk.CTkLabel(self, text=title_text, font=("Arial", 28, "bold")).pack(pady=5)

        # File Selection
        self.f_frame = ctk.CTkFrame(self)
        self.f_frame.pack(pady=10, padx=40, fill="x")
        
        self.btn_f1 = ctk.CTkButton(self.f_frame, text="رفع المواصفات (Spec)" if self.lang=="AR" else "Upload Spec", command=lambda: self.select_file(1))
        self.btn_f1.pack(side="left", expand=True, padx=10, pady=15)
        
        self.btn_f2 = ctk.CTkButton(self.f_frame, text="رفع العرض (Offer)" if self.lang=="AR" else "Upload Offer", command=lambda: self.select_file(2))
        self.btn_f2.pack(side="left", expand=True, padx=10, pady=15)

        self.lbl_info = ctk.CTkLabel(self, text="Status: Ready / جاهز", text_color="gray")
        self.lbl_info.pack()

        # Results Table (6 Columns)
        self.tree_frame = ctk.CTkFrame(self)
        self.tree_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        cols = ("sec", "spec_text", "offer_text", "stat", "gap", "rem")
        self.tree = ttk.Treeview(self.tree_frame, columns=cols, show="headings")
        
        # ترويسة الأعمدة الستة
        headings = {
            "sec": ("البند", "Section"),
            "spec_text": ("المواصفة المطلوبة", "Required Spec"),
            "offer_text": ("الوصف المقدم", "Offered Description"),
            "stat": ("الحالة", "Status"),
            "gap": ("الفوارق الفنية", "Technical Gap"),
            "rem": ("ملاحظة المستشار", "Consultant Remark")
        }

        for col, (ar, en) in headings.items():
            self.tree.heading(col, text=f"{ar} / {en}")
            width = 100 if col in ["sec", "stat"] else 250
            self.tree.column(col, width=width, anchor="center" if col in ["sec", "stat"] else "w")

        self.tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        sb.pack(side="right", fill="y")

        # Progress
        self.progress = ctk.CTkProgressBar(self, width=800)
        self.progress.pack(pady=10)
        self.progress.set(0)

        # Actions
        self.btn_run = ctk.CTkButton(self, text="بدء التحليل الفني الشامل" if self.lang=="AR" else "Run Deep Analysis", fg_color="#d35400", height=50, command=self.start_analysis)
        self.btn_run.pack(pady=10)
        
        self.btn_save = ctk.CTkButton(self, text="تصدير التقرير (Excel)" if self.lang=="AR" else "Export Excel", fg_color="#27ae60", height=45, state="disabled", command=self.save_excel)
        self.btn_save.pack(pady=5)

    def toggle_lang(self):
        self.lang = "EN" if self.lang=="AR" else "AR"
        self.setup_ui()

    def select_file(self, n):
        p = filedialog.askopenfilename()
        if p:
            if n==1: self.file1_path = p
            else: self.file2_path = p
            self.lbl_info.configure(text=f"Selected Files: {os.path.basename(self.file1_path or '')} & {os.path.basename(self.file2_path or '')}", text_color="#2ecc71")

    def start_analysis(self):
        if not self.file1_path or not self.file2_path:
            return messagebox.showwarning("!", "Please select files!")
        threading.Thread(target=self.analysis_logic, daemon=True).start()

    def analysis_logic(self):
        self.btn_run.configure(state="disabled")
        for i in self.tree.get_children(): self.tree.delete(i)
        self.final_data = []

        try:
            doc1 = fitz.open(self.file1_path)
            doc2 = fitz.open(self.file2_path)
            total = min(len(doc1), len(doc2))

            for i in range(total):
                self.lbl_info.configure(text=f"Analyzing Item/Page {i+1}...")
                txt1 = doc1[i].get_text()[:2000]
                txt2 = doc2[i].get_text()[:2000]

                if not txt1.strip(): continue

                # تطوير الـ Prompt ليخرج الـ 6 أعمدة بدقة
                prompt = f"""
                Compare Engineering Documents Page by Page.
                FORMAT: Section || Required Spec || Offered Description || Status || Technical Gap || Remark
                
                Document 1 (Spec): {txt1}
                Document 2 (Offer): {txt2}
                """

                response = g4f.ChatCompletion.create(model=g4f.models.default, messages=[{"role": "user", "content": prompt}])

                for line in response.split('\n'):
                    if "||" in line:
                        parts = [p.strip() for p in line.split("||")]
                        if len(parts) >= 6:
                            row = parts[:6]
                            self.final_data.append(row)
                            self.tree.insert("", "end", values=row)
                
                self.progress.set((i + 1) / total)

            self.btn_save.configure(state="normal")
            self.lbl_info.configure(text="Analysis Complete!", text_color="#2ecc71")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        
        self.btn_run.configure(state="normal")

    def save_excel(self):
        path = filedialog.asksaveasfilename(defaultextension=".xlsx")
        if path:
            headers = ["Section", "Required Specification", "Offered Description", "Status", "Technical Gap", "Consultant Remark"]
            pd.DataFrame(self.final_data, columns=headers).to_excel(path, index=False)
            messagebox.showinfo("Done", "Comprehensive Report Saved!")

if __name__ == "__main__":
    app = FullComparisonApp()
    app.mainloop()