#!/usr/bin/env python3
"""
Generate and save Mermaid diagram from LangGraph chatbot
"""

import os
import sys
from pathlib import Path
from akv import AzureKeyVault

akv = AzureKeyVault()
os.environ["OPENAI_API_KEY"] = akv.get_secret("openai-apikey")

# Add the current directory to the path so we can import the chatbot
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_agents.langgraph_chatbot import graph


def generate_mermaid_diagram():
    """Generate and save the Mermaid diagram from the LangGraph chatbot"""
    
    print("🎨 Generating Mermaid diagram from LangGraph chatbot...")
    
    try:
        # Get the graph object
        graph_obj = graph.get_graph()
        
        # Generate Mermaid PNG
        print("📊 Creating Mermaid diagram...")
        mermaid_png = graph_obj.draw_mermaid_png()
        
        # Save the diagram
        output_path = Path("langgraph_chatbot_diagram.png")
        
        with open(output_path, "wb") as f:
            f.write(mermaid_png)
        
        print(f"✅ Mermaid diagram saved successfully to: {output_path.absolute()}")
        print(f"📁 File size: {len(mermaid_png)} bytes")
        
        return output_path
        
    except Exception as e:
        print(f"❌ Error generating Mermaid diagram: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("🚀 LangGraph Chatbot Mermaid Diagram Generator")
    print("=" * 50)
    
    # Generate the diagram
    png_path = generate_mermaid_diagram()
    
    if png_path:
        print(f"\n🎉 Success! Diagram saved to: {png_path}")
    else:
        print("\n💥 Failed to generate diagram. Check the error messages above.")
    
    print("\n🏁 Diagram generation completed!")
    
