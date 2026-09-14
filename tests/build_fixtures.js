// Entirely synthetic; no personal or client assets. Fonts installed by CI.
const P=require('pptxgenjs'),fs=require('fs'),path=require('path');
// Test-only mitigation: never enable parsers for untrusted/unsupported image types.
const imageSize=require('image-size');
imageSize.disableTypes(imageSize.types.filter(t=>t!=='png'));
const out=process.argv[2];if(!out)throw Error('Output directory required');
async function build(name,w,h,vertical){
 const p=new P();p.defineLayout({name:'TEST',width:w,height:h});p.layout='TEST';p.author='Synthetic CI';p.title=name;
 p.theme={headFontFace:'Noto Sans CJK SC',bodyFontFace:'Noto Sans CJK SC',lang:'zh-CN'};
 const font='Noto Sans CJK SC',ink='18383D',accent='087F8C';
 function text(s,v,x,y,ww,hh,size=18){s.addText(v,{x,y,w:ww,h:hh,fontFace:font,fontSize:size,color:ink,margin:0});}
 function slide(title){const s=p.addSlide();s.background={color:'FFFFFF'};text(s,title,.6,.55,w-1.2,.6,28);text(s,'模拟测试 / Synthetic fixture',.6,h-.45,w-1.2,.25,10);s.addNotes('Synthetic input; not production evidence.');return s;}
 let s=slide('从输入到结果');
 const labels=['输入','处理','结果'],nw=vertical?2.4:2.1,nh=.7,gap=vertical?.85:.5;
 labels.forEach((v,i)=>{const x=vertical?.8:.7+i*(nw+gap),y=vertical?2+i*(nh+gap):2.4;
  s.addText(v,{shape:p.ShapeType.roundRect,x,y,w:nw,h:nh,fontFace:font,fontSize:20,align:'center',valign:'mid',margin:.06,fill:{color:'EAF4F5'},line:{color:accent,width:1}});
  if(i<2)s.addShape(p.ShapeType.line,{x:vertical?x+nw/2:x+nw,y:vertical?y+nh:y+nh/2,w:vertical?0:gap,h:vertical?gap:0,line:{color:accent,width:1.5,endArrowType:'triangle'}});
 });
 if(vertical)text(s,'不同形态，共用验证规则。',3.7,2.2,w-4.3,1,18);
 else text(s,'真实箭头与可编辑文字；不以整页图片替代。',.7,4.1,w-1.4,.9,20);
 s=slide('数据与素材均可追溯');
 s.addChart(p.ChartType.bar,[{name:'模拟完成次数',labels:['A','B'],values:[6,8]}],{x:.7,y:1.7,w:w-1.4,h:vertical?3.1:2.4,barDir:'col',showLegend:false,showValue:true,dataLabelPosition:'outEnd',valAxisMinVal:0,valAxisMaxVal:10,valAxisMajorUnit:2,chartColors:[accent],catAxisLabelFontFace:font,valAxisLabelFontFace:font,catAxisLabelFontSize:13,valAxisLabelFontSize:12});
 s.addImage({path:path.join(out,'synthetic.png'),x:.8,y:vertical?5.1:4.5,w:2,h:1.125});
 text(s,'图像：程序生成的色块\n数据：6 与 8 次，仅为模拟',3.2,vertical?5.1:4.5,w-3.8,1.1,17);
 s=slide('建议先验证，再推广');
 const rows=[['编号','规则','状态'],...Array.from({length:5},(_,i)=>[`R0${i+1}`,['数据源可用','异常可恢复','权限需校验','状态可追踪','结果可复核'][i],'模拟规划'])];
 s.addTable(rows,{x:.65,y:1.75,w:w-1.3,colW:[1.2,w-4.2,1.7],rowH:.55,fontFace:font,fontSize:16,margin:.1,border:{color:'C8D5D9',pt:.7},autoPage:false});
 const f=path.join(out,name+'.pptx');if(fs.existsSync(f))throw Error('Refusing overwrite');await p.writeFile({fileName:f});
}
(async()=>{await build('wide',13.333333,7.5,false);await build('standard',10,7.5,false);await build('portrait',8.2677,11.6929,true)})().catch(e=>{console.error(e);process.exit(1)});
