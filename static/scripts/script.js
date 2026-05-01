const likeBtn = document.querySelectorAll(".like");
likeBtn.forEach((btn) => {
    btn.addEventListener("click", (e) => {
        let xhr = new XMLHttpRequest();
        let formData = new FormData();
        formData.append("id", btn.dataset.id);
        xhr.open("POST", "/like");
        xhr.send(formData);
        xhr.onload = () => {
            if (JSON.parse(xhr.response).response == "created") {
                btn.textContent = `like ${(parseInt(btn.textContent.split(" ")[1]) + 1)}`;
            } else {
                btn.textContent = `like ${(parseInt(btn.textContent.split(" ")[1]) - 1)}`;
            }
        }
    })
})

const dislikeBtn = document.querySelectorAll(".dislike");
dislikeBtn.forEach((btn) => {
    btn.addEventListener("click", (e) => {
        let xhr = new XMLHttpRequest();
        let formData = new FormData();
        formData.append("id", btn.dataset.id);
        xhr.open("POST", "/dislike");
        xhr.send(formData);
        xhr.onload = () => {
            if (JSON.parse(xhr.response).response == "created") {
                btn.textContent = `dislike ${(parseInt(btn.textContent.split(" ")[1]) + 1)}`;
            } else {
                btn.textContent = `dislike ${(parseInt(btn.textContent.split(" ")[1]) - 1)}`;
            }
        }
    })
})

