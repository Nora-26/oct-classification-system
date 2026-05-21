from graphviz import Digraph

# 创建有向图，从上到下布局，输出 SVG 矢量图
dot = Digraph(format='svg', engine='dot')
dot.attr(rankdir='TB', fontname='SimHei', fontsize='14')
dot.attr('node', shape='box', style='rounded,filled', fillcolor='#E8F0FE', fontname='SimHei', fontsize='12')

def add_node(name, label):
    dot.node(name, label)

# 定义各模块（基于输入 512×512 的尺寸）
add_node('input', 'Input\n灰度图像 (1×512×512)')
add_node('stem', 'Stem\nConv3×3, stride2, BN, Swish\n输出: 32×256×256')
add_node('s1', 'Stage1: MBConv1 (×1)\nk3×3, expand=1, stride1\n输出: 16×256×256')
add_node('s2', 'Stage2: MBConv2 (×2)\nk3×3, expand=6, stride2\n输出: 24×128×128')
add_node('s3', 'Stage3: MBConv3 (×2)\nk5×5, expand=6, stride2\n输出: 40×64×64')
add_node('s4', 'Stage4: MBConv4 (×3)\nk3×3, expand=6, stride2\n输出: 80×32×32')
add_node('s5', 'Stage5: MBConv5 (×3)\nk5×5, expand=6, stride1\n输出: 112×32×32')
add_node('s6', 'Stage6: MBConv6 (×4)\nk5×5, expand=6, stride2\n输出: 192×16×16')
add_node('s7', 'Stage7: MBConv7 (×1)\nk3×3, expand=6, stride1\n输出: 320×16×16')
add_node('head', 'Head\nConv1×1, BN, Swish\n输出: 1280×16×16')
add_node('gap', 'Global Average Pooling\n输出: 1280 维向量')
add_node('drop', 'Dropout (p=0.2)')
add_node('fc', 'Fully Connected\n1280 → 4')
add_node('softmax', 'Softmax')
add_node('output', '输出\nNORMAL / CNV / DME / DRUSEN')

# 连接顺序
nodes = ['input', 'stem', 's1', 's2', 's3', 's4', 's5', 's6', 's7',
         'head', 'gap', 'drop', 'fc', 'softmax', 'output']
for i in range(len(nodes)-1):
    dot.edge(nodes[i], nodes[i+1])

# 渲染
dot.render('model_structure_graphviz', view=False, cleanup=True)
print("模型结构图已保存为 model_structure_graphviz.svg")