# Live2D 模型目录

在此目录下放入你的 Live2D 模型文件。

## 模型结构

每个模型应该放在单独的子目录中：

```
assets/live2d/
└── my_model/
    ├── my_model.model3.json
    ├── my_model.physics3.json
    ├── my_model.pose3.json
    ├── my_model.cdi3.json
    ├── motions/
    │   ├── idle_01.motion3.json
    │   └── ...
    └── expressions/
        ├── happy.exp3.json
        └── ...
```

## 快速开始

如果暂时没有 Live2D 模型，程序会使用占位渲染。
你可以在设置中随时更换模型路径。
