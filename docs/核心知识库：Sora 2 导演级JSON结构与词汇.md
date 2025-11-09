# **核心知识库：Sora 2 导演级JSON结构与词汇**

## **1\. 核心JSON结构：导演级工作流**

### **1.1 从“剧本”到“故事板”**

你的核心任务是生成“故事板”（Shot List），而非“剧本”（Script）。这意味着必须将用户的单一“剧本”分解为独立的、原子的“镜头”（shots）任务。



## **2\. 专业词汇库：风格、表演与镜头**

在填充JSON时，你必须优先使用以下专业词汇。

### **2.1 动画与艺术风格 (Animation & Art Style)**

* **皮克斯/3D (Pixar/3D)**: Pixar animated short, 3D render, stylized 3D animation, painted-toon hybrid, high-end TV commercial.  
* **日本动画/2D (Anime/2D)**: In the style of a Japanese anime, Ghibli style, 2D animation, sakuga animation (高张力作画), fluid hand-drawn motion, zany comedy 'Gintama' style.  
* **其他风格 (Other Styles)**: stop-motion claymation, South Park style, King of the Hill, watercolor style.

### **2.2 喜剧与表演 (Comedy & Performance)**

* **风格**: slapstick comedy (闹剧), zany (荒诞), manzai (漫才), Tarantino-style (昆汀风格), Wes Anderson symmetry (韦斯·安德森式对称).  
* **面部表情 (Facial Expressions)**: expression shifts from neutral to shocked (表情从呆滞变为震惊), wry smile (苦笑), deadpan expression (面无表情), confused (困惑), exaggerated gasp (夸张倒抽气), crying face (哭丧着脸).  
* **肢体语言 (Body Language)**: shoulders slumped in defeat (垂头SANG气), rubs his sore backside (揉着酸痛的屁股), gestures wildly (手舞足蹈), facepalms (捂脸).

### **2.3 镜头与调度 (Camera & Cinematography)**

| 用户通俗描述 | 专业提示词 (Professional Prompt) |
| :---- | :---- |
| 中景/全景 | Medium shot (MS) 或 Medium full shot (MFS) |
| 近景/特写 | Close-up (CU) 或 Medium close-up (MCU) |
| 俯拍 | Bird's eye view 或 High angle shot |
| 跟随拍摄 | Tracking shot (跟随) 或 Steadicam shot (稳定器) |
| 其他常用 | Over-the-shoulder (OTS) (过肩镜头), Low angle shot (低角度) |
| 其他常用 | Handheld shaky cam (手持晃动), Slow dolly-in (缓慢推近) |
| 细节特写 | Extreme close-up (ECU) |
| 快速插入 | Insert shots |

### **2.4 灯光与氛围 (Lighting & Atmosphere)**

* **关键词**: low key lighting (低调照明，高对比度), flickering torchlight (闪烁的火光), warm candlelight (温暖的烛光), dramatic backlit (戏剧性背光), volumetric light (体积光), neon signs reflecting in puddles (霓虹灯在水坑中的反射).  
* **色调 (Palette)**: Palette anchors: amber, cream, walnut brown (色调锚点：琥珀色、奶油色、胡桃棕).

## **3\. 高级指令：对话、音效与节拍**

### **3.1 对话与口型同步 (Dialogue & Lip-Sync)**

* **最佳实践**: 必须使用专用的 Dialogue: { "character": "...", "line": "...", "tone": "..." } 结构。  
* **指定表演**: 在tone中包含语气和口音。  
* **解决混淆**: 确保执行口型同步的shot，其input\_reference是该角色的“特写参考图像”，并且cinematography是“Close-up” 或 “MCU”。这是Sora 2识别“谁在说话”的最可靠方法。

### **3.2 音效与音乐 (Sound Effects & Music)**

* 如果用户提到，或场景强烈暗示，**必须**使用 audio 键指定。  
* **示例**: Audio: Loud thunder crash, Audio: subtle wind chimes, Audio: muffled sounds from inside car, Audio: crackling torchlight, distant shouting, subtle metallic clinking of armor.

### **3.3 拥抱“节拍”控制**

Sora 2对“动作节拍” (Beats) 的理解远胜于“时间戳”。在 performance 字段中，优先使用基于“节拍”的描述。

* **弱提示 (避免)**: 3.0\~6.0秒：汤小团...  
* **强提示 (使用)**: performance: "Close-up on Tang. Beat 1: His eyes widen. Beat 2: He gasps and starts whispering urgently."