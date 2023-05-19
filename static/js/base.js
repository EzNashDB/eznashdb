(function setBodyHeight(){
    function resetBodyHeight(){
        document.body.style.height = window.innerHeight + "px";
    }
    window.addEventListener("resize", resetBodyHeight);
    resetBodyHeight();
})();
