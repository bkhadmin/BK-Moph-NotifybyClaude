function filterTable(inputId, tableId){
  const q=document.getElementById(inputId).value.toLowerCase()
  const rows=document.querySelectorAll(`#${tableId} tbody tr`)
  rows.forEach(r=>{
    const txt=r.innerText.toLowerCase()
    r.style.display=txt.includes(q)?'':'none'
  })
}
