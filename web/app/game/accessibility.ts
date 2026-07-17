export function nextFocusIndex(current:number,count:number,direction:1|-1){if(count<=0)return-1;if(current<0)return direction===1?0:count-1;return(current+direction+count)%count}
export function isActivationButton(index:number){return index===0||index===1}
