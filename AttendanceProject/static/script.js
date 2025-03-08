document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".mark-attendance-btn").forEach(button => {
        button.addEventListener("click", function () {
            let studentId = this.dataset.studentId; 
            let courseId = this.dataset.courseId;
            
            fetch("/mark_attendance", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ student_id: studentId, course_id: courseId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.textContent = "✔ تم تسجيل الحضور";  
                    this.disabled = true;  
                    let statusSpan = document.querySelector(`#attendance-status-${studentId}`);
                    if (statusSpan) {
                        statusSpan.textContent = "حاضر";
                        statusSpan.style.color = "green";
                    }
                } else {
                    alert("حدث خطأ أثناء تسجيل الحضور!");
                }
            })
            .catch(error => console.error("Error:", error));
        });
    });
});
