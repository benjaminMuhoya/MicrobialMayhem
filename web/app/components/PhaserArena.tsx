"use client";

import { useEffect, useRef } from "react";

export function PhaserArena({ reducedMotion = false }: { reducedMotion?: boolean }) {
  const host = useRef<HTMLDivElement>(null);
  useEffect(() => {
    let game: import("phaser").Game | undefined;
    let disposed = false;
    void import("phaser").then(({ default: Phaser }) => {
      if (disposed || !host.current) return;
      class LivingArena extends Phaser.Scene {
        left!: Phaser.GameObjects.Container; right!: Phaser.GameObjects.Container; impact!: Phaser.GameObjects.Arc;
        createCell(x:number,y:number,color:number,flip=false){
          const body=this.add.ellipse(0,0,210,118,color,.36).setStrokeStyle(4,color,.95);
          const core=this.add.ellipse(-18,0,72,38,color,.7); const spots=[[-55,-22],[35,-28],[62,18]].map(([sx,sy])=>this.add.circle(sx,sy,5,0xffffff,.8));
          const tail=this.add.graphics().lineStyle(4,color,.8); const side=flip?-1:1;
          tail.lineBetween(side*102,0,side*145,-28).lineBetween(side*145,-28,side*184,-24).lineBetween(side*184,-24,side*220,15);
          const container=this.add.container(x,y,[tail,body,core,...spots]); if(flip)container.setScale(-1,1); return container;
        }
        create(){
          const {width,height}=this.scale; const bg=this.add.graphics(); bg.fillGradientStyle(0x0a241d,0x0a241d,0x321b16,0x321b16,1); bg.fillRect(0,0,width,height);
          for(let i=0;i<28;i++){const p=this.add.circle((i*83)%width,80+(i*59)%(height-130),2+(i%4),i%3?0xff755f:0x7bf2bc,.25); if(!reducedMotion)this.tweens.add({targets:p,y:p.y-32,duration:1800+(i%5)*380,yoyo:true,repeat:-1,ease:"Sine.inOut",delay:i*70});}
          this.left=this.createCell(width*.27,height*.56,0xff755f); this.right=this.createCell(width*.73,height*.54,0x7bf2bc,true);
          this.left.x=-180; this.right.x=width+180; this.tweens.add({targets:this.left,x:width*.27,duration:reducedMotion?80:650,ease:"Back.out"}); this.tweens.add({targets:this.right,x:width*.73,duration:reducedMotion?80:650,ease:"Back.out"});
          this.impact=this.add.circle(width*.5,height*.48,8,0xd7f171,.8); this.impact.setVisible(false);
          this.time.delayedCall(reducedMotion?100:1100,()=>this.attack());
        }
        attack(){const {width}=this.scale; this.tweens.add({targets:this.left,x:width*.43,duration:reducedMotion?70:260,ease:"Cubic.in",yoyo:true,hold:70,onYoyo:()=>{this.impact.setVisible(true);this.tweens.add({targets:this.impact,scale:10,alpha:0,duration:reducedMotion?80:420,onComplete:()=>this.impact.setVisible(false)});this.cameras.main.shake(reducedMotion?0:110,.006);this.tweens.add({targets:this.right,x:"+=28",angle:5,duration:120,yoyo:true});}});}
      }
      game=new Phaser.Game({type:Phaser.AUTO,parent:host.current!,transparent:true,width:1000,height:460,scene:LivingArena,scale:{mode:Phaser.Scale.FIT,autoCenter:Phaser.Scale.CENTER_BOTH},render:{antialias:true,pixelArt:false},audio:{noAudio:true}});
    });
    return()=>{disposed=true;game?.destroy(true)};
  },[reducedMotion]);
  return <div ref={host} className="phaser-arena" role="img" aria-label="Scripted microscopic battle between two procedural bacterial fighters"/>;
}
