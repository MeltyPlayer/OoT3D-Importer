// Decompiled with JetBrains decompiler
// Type: CMABExtractor.Program
// Assembly: CMABExtractor, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null
// MVID: F31EBCCA-BB47-4828-8339-39147FE028DD
// Assembly location: R:\Documents\PythonWorkspace\OoT3D-Importer\test_data\CMABExtractor.exe

using System;
using System.Windows.Forms;

namespace CMABExtractor
{
  internal static class Program
  {
    [STAThread]
    private static void Main()
    {
      Application.EnableVisualStyles();
      Application.SetCompatibleTextRenderingDefault(false);
      Application.Run((Form) new Form1());
    }
  }
}
