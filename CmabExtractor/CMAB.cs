// Decompiled with JetBrains decompiler
// Type: CMABExtractor.CMAB
// Assembly: CMABExtractor, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null
// MVID: F31EBCCA-BB47-4828-8339-39147FE028DD
// Assembly location: R:\Documents\PythonWorkspace\OoT3D-Importer\test_data\CMABExtractor.exe

using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace CMABExtractor
{
  internal class CMAB
  {
    public List<CMABFile> Files = new List<CMABFile>();

    public CMAB(string FilePath)
    {
      using (FileStream Stream = new FileStream(FilePath, FileMode.Open, FileAccess.Read))
      {
        BinaryReader binaryReader = new BinaryReader((Stream) Stream);
        if (!(Encoding.ASCII.GetString(BitConverter.GetBytes(binaryReader.ReadInt32())) == "cmab"))
          throw new FileLoadException("Opened file is not a CMAB archive!");
        binaryReader.ReadInt32();
        binaryReader.ReadInt32();
        binaryReader.ReadInt32();
        binaryReader.ReadInt32();
        int num1 = binaryReader.ReadInt32();
        int num2 = binaryReader.ReadInt32();
        int num3 = binaryReader.ReadInt32();
        if (binaryReader.ReadUInt32() != uint.MaxValue)
          throw new Exception("'0xFFFFFFFF' not found!");
        binaryReader.ReadInt32();
        binaryReader.ReadInt32();
        binaryReader.ReadInt32();
        int num4 = binaryReader.ReadInt32();
        Stream.Seek((long) (num1 + num4), SeekOrigin.Begin);
        if (!(Encoding.ASCII.GetString(BitConverter.GetBytes(binaryReader.ReadInt32())) == "txpt"))
          throw new Exception("'txpt' not found!");
        int num5 = binaryReader.ReadInt32();
        for (int index = 0; index < num5; ++index)
          this.Files.Add(new CMABFile()
          {
            Size = binaryReader.ReadInt32(),
            Unknown1 = binaryReader.ReadInt16(),
            Unknown2 = binaryReader.ReadInt16(),
            Width = binaryReader.ReadInt16(),
            Height = binaryReader.ReadInt16(),
            Format = binaryReader.ReadUInt32(),
            Offset = binaryReader.ReadInt32() + num3,
            Id = binaryReader.ReadInt32()
          });
        if (!(Encoding.ASCII.GetString(BitConverter.GetBytes(binaryReader.ReadInt32())) == "strt"))
          throw new Exception("'strt' not found!");
        int num6 = binaryReader.ReadInt32();
        for (int index = 0; index < num6; ++index)
        {
          Stream.Seek((long) (num2 + index * 4 + 8), SeekOrigin.Begin);
          int num7 = binaryReader.ReadInt32();
          Stream.Seek((long) (num2 + num6 * 4 + 8 + num7), SeekOrigin.Begin);
          this.Files[index].Name = Stream.ReadNullTerminatedString();
        }
      }
    }
  }
}
