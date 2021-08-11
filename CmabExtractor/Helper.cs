// Decompiled with JetBrains decompiler
// Type: CMABExtractor.Helper
// Assembly: CMABExtractor, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null
// MVID: F31EBCCA-BB47-4828-8339-39147FE028DD
// Assembly location: R:\Documents\PythonWorkspace\OoT3D-Importer\test_data\CMABExtractor.exe

using System.Collections.Generic;
using System.IO;
using System.Text;

namespace CMABExtractor
{
  public static class Helper
  {
    public static string ReadNullTerminatedString(this Stream Stream)
    {
      List<byte> byteList = new List<byte>();
      int num;
      while ((num = Stream.ReadByte()) != 0)
        byteList.Add((byte) num);
      return Encoding.ASCII.GetString(byteList.ToArray());
    }
  }
}
