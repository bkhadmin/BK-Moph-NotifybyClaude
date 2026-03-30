function esc(v){
  return String(v ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;')
}

function _sizeMap(s){
  return {xxs:'.65rem',xs:'.72rem',sm:'.78rem',md:'.84rem',lg:'.92rem',xl:'1rem',xxl:'1.1rem','3xl':'1.25rem','4xl':'1.4rem','5xl':'1.6rem'}[s] || '.84rem'
}
function _colorOrDefault(c, def){ return (c && /^#/.test(c)) ? c : def }

function _renderContents(contents, level){
  level = level || 0
  if(!Array.isArray(contents)) return ''
  let html = ''
  contents.forEach(function(c){
    if(!c || !c.type) return
    if(c.type === 'text'){
      var style = []
      if(c.size) style.push('font-size:'+_sizeMap(c.size))
      if(c.color) style.push('color:'+_colorOrDefault(c.color,'#0f172a'))
      if(c.weight === 'bold') style.push('font-weight:700')
      if(c.align) style.push('text-align:'+c.align)
      if(c.margin) style.push('margin-top:'+(c.margin==='sm'?'4px':c.margin==='md'?'8px':c.margin==='lg'?'14px':c.margin==='xl'?'20px':'6px'))
      if(c.wrap === false) style.push('white-space:nowrap;overflow:hidden;text-overflow:ellipsis')
      html += '<div style="'+(style.join(';'))+'">'+esc(c.text || '')+'</div>'
    } else if(c.type === 'box'){
      var bstyle = []
      if(c.layout === 'horizontal') bstyle.push('display:flex;flex-direction:row;align-items:center;gap:6px')
      if(c.margin) bstyle.push('margin-top:'+(c.margin==='sm'?'4px':c.margin==='md'?'8px':c.margin==='lg'?'14px':c.margin==='xl'?'20px':'6px'))
      if(c.paddingAll || c.padding) bstyle.push('padding:'+(c.paddingAll||c.padding))
      if(c.backgroundColor) bstyle.push('background:'+_colorOrDefault(c.backgroundColor,'transparent')+';border-radius:6px')
      html += '<div style="'+(bstyle.join(';'))+'">' + _renderContents(c.contents, level+1) + '</div>'
    } else if(c.type === 'separator'){
      var scolor = _colorOrDefault(c.color, '#e2e8f0')
      html += '<hr style="border:none;border-top:1px solid '+scolor+';margin:6px 0">'
    } else if(c.type === 'image'){
      html += '<div style="background:#e2e8f0;border-radius:6px;text-align:center;padding:10px 0;font-size:.72rem;color:#94a3b8;margin:4px 0">🖼 IMAGE</div>'
    } else if(c.type === 'button'){
      var blabel = (c.action && c.action.label) ? c.action.label : 'Button'
      var bcolor = _colorOrDefault(c.color, '#2563eb')
      var bstyle2 = 'display:block;width:100%;padding:8px;background:'+bcolor+';color:#fff;border:none;border-radius:8px;font-size:.8rem;font-weight:700;text-align:center;cursor:default;margin-top:6px'
      if(c.style === 'secondary') bstyle2 = 'display:block;width:100%;padding:8px;background:#f1f5f9;color:#334155;border:none;border-radius:8px;font-size:.8rem;font-weight:700;text-align:center;cursor:default;margin-top:6px'
      if(c.style === 'link') bstyle2 = 'display:block;width:100%;padding:8px;background:transparent;color:'+bcolor+';border:none;font-size:.8rem;font-weight:700;text-align:center;cursor:default;margin-top:6px'
      html += '<button style="'+bstyle2+'">'+esc(blabel)+'</button>'
    }
  })
  return html
}

function renderFlexPreview(textareaId, previewId){
  const box = document.getElementById(previewId)
  if(!box) return
  const raw = (document.getElementById(textareaId)||{}).value || ''
  if(!raw.trim()){ box.innerHTML = '<div style="color:#94a3b8;font-size:.82rem;font-style:italic;padding:12px 0">พิมพ์ Flex JSON เพื่อดูตัวอย่าง</div>'; return }
  try{
    const json = JSON.parse(raw)
    // support both bubble directly or {type:"flex", contents:{type:"bubble",...}}
    const bubble = (json.type === 'flex' && json.contents) ? json.contents : json

    let html = '<div class="fp-phone"><div class="fp-bubble">'

    // header
    if(bubble.header && bubble.header.contents){
      html += '<div class="fp-header">' + _renderContents(bubble.header.contents) + '</div>'
    }
    // hero
    if(bubble.hero){
      if(bubble.hero.url){
        html += '<div style="background:#e2e8f0;text-align:center;padding:14px 0;font-size:.72rem;color:#94a3b8">🖼 Hero Image</div>'
      }
    }
    // body
    if(bubble.body && bubble.body.contents){
      html += '<div class="fp-body">' + _renderContents(bubble.body.contents) + '</div>'
    }
    // footer
    if(bubble.footer && bubble.footer.contents){
      html += '<div class="fp-footer">' + _renderContents(bubble.footer.contents) + '</div>'
    }

    html += '</div></div>'
    box.innerHTML = html
  } catch(e){
    box.innerHTML = '<div style="color:#dc2626;font-size:.78rem;padding:8px 0">⚠ JSON ไม่ถูกต้อง: '+esc(e.message)+'</div>'
  }
}
