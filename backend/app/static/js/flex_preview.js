function esc(v){
  return String(v ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;')
}
function renderFlexPreview(textareaId, previewId){
  const box = document.getElementById(previewId)
  try{
    const json=JSON.parse(document.getElementById(textareaId).value)
    let html='<div class="line-phone"><div class="line-bubble">'
    if(json.hero && json.hero.url){
      html+=`<div class="line-hero">IMAGE</div>`
    }
    const body=json.body?.contents||[]
    body.forEach(c=>{
      if(c.type==='text'){
        const cls = (c.weight==='bold' ? ' flex-text-bold' : '')
        html+=`<div class="flex-text${cls}">${esc(c.text)}</div>`
      }
      if(c.type==='separator'){
        html+=`<div class="flex-sep"></div>`
      }
    })
    if(json.footer?.contents?.length){
      html+='<div class="flex-footer">'
      json.footer.contents.forEach(c=>{
        if(c.type==='button'){
          html+=`<button class="flex-btn">${esc(c.action?.label || 'Button')}</button>`
        }
        if(c.type==='text'){
          html+=`<div class="flex-footer-text">${esc(c.text)}</div>`
        }
      })
      html+='</div>'
    }
    html+='</div></div>'
    box.innerHTML=html
  }catch(e){
    box.innerHTML='<div class="muted">invalid json</div>'
  }
}
