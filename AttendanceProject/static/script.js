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
                    const button = document.querySelector(`button[data-student-id="${studentId}"].mark-absent-btn`);
                    if (button) {
                        button.removeAttribute('disabled');
                        button.textContent = 'تسجيل الغياب ';
                    }
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
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".mark-absent-btn").forEach(button => {
        button.addEventListener("click", function () {
            let studentId = this.dataset.studentId; 
            let courseId = this.dataset.courseId;
            
            fetch("/mark_absent", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ student_id: studentId, course_id: courseId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.textContent = "✔ تم تسجيل الغياب";  
                    this.disabled = true;
                    const button = document.querySelector(`button[data-student-id="${studentId}"].mark-attendance-btn`);
                    if (button) {
                        button.removeAttribute('disabled');
                        button.textContent = 'تسجيل الحضور ';
                    }
                    let statusSpan = document.querySelector(`#attendance-status-${studentId}`);
                    if (statusSpan) {
                        statusSpan.textContent = "غائب";
                        statusSpan.style.color = "red";
                    }
                } else {
                    alert("حدث خطأ أثناء تسجيل الغياب!");
                }
            })
            .catch(error => console.error("Error:", error));
        });
    });
});
