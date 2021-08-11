// Decompiled with JetBrains decompiler
// Type: CMABExtractor.TextureDecoder
// Assembly: CMABExtractor, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null
// MVID: F31EBCCA-BB47-4828-8339-39147FE028DD
// Assembly location: R:\Documents\PythonWorkspace\OoT3D-Importer\test_data\CMABExtractor.exe

using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.Linq;
using System.Runtime.InteropServices;

namespace CMABExtractor
{
  internal class TextureDecoder
  {
    private static int[] tileOrder = new int[64]
    {
      0,
      1,
      8,
      9,
      2,
      3,
      10,
      11,
      16,
      17,
      24,
      25,
      18,
      19,
      26,
      27,
      4,
      5,
      12,
      13,
      6,
      7,
      14,
      15,
      20,
      21,
      28,
      29,
      22,
      23,
      30,
      31,
      32,
      33,
      40,
      41,
      34,
      35,
      42,
      43,
      48,
      49,
      56,
      57,
      50,
      51,
      58,
      59,
      36,
      37,
      44,
      45,
      38,
      39,
      46,
      47,
      52,
      53,
      60,
      61,
      54,
      55,
      62,
      63
    };
    private static int[,] etc1LUT = new int[8, 4]
    {
      {
        2,
        8,
        -2,
        -8
      },
      {
        5,
        17,
        -5,
        -17
      },
      {
        9,
        29,
        -9,
        -29
      },
      {
        13,
        42,
        -13,
        -42
      },
      {
        18,
        60,
        -18,
        -60
      },
      {
        24,
        80,
        -24,
        -80
      },
      {
        33,
        106,
        -33,
        -106
      },
      {
        47,
        183,
        -47,
        -183
      }
    };

    public static TextureFormat GetFormat(uint value)
    {
      if (!Enum.IsDefined(typeof (TextureFormat), (object) value))
        throw new Exception(string.Format("Texture format '0x{0:x}'not supported, contact Ac_K !", (object) value));
      return (TextureFormat) value;
    }

    public static Bitmap Decode(byte[] data, int width, int height, TextureFormat format)
    {
      byte[] numArray1 = new byte[width * height * 4];
      long index1 = 0;
      bool flag = false;
      switch (format)
      {
        case TextureFormat.ETC1:
        case TextureFormat.ETC1A4:
          byte[] numArray2 = TextureDecoder.etc1Decode(data, width, height, format == TextureFormat.ETC1A4);
          int[] numArray3 = TextureDecoder.etc1Scramble(width, height);
          int index2 = 0;
          for (int index3 = 0; index3 < height / 4; ++index3)
          {
            for (int index4 = 0; index4 < width / 4; ++index4)
            {
              int num1 = numArray3[index2] % (width / 4);
              int num2 = (numArray3[index2] - num1) / (width / 4);
              for (int index5 = 0; index5 < 4; ++index5)
              {
                for (int index6 = 0; index6 < 4; ++index6)
                {
                  long num3 = (long) ((num1 * 4 + index6 + (num2 * 4 + index5) * width) * 4);
                  long num4 = (long) ((index4 * 4 + index6 + (index3 * 4 + index5) * width) * 4);
                  Buffer.BlockCopy((Array) numArray2, (int) num3, (Array) numArray1, (int) num4, 4);
                }
              }
              ++index2;
            }
          }
          break;
        case TextureFormat.RGBA8:
          for (int index3 = 0; index3 < height / 8; ++index3)
          {
            for (int index4 = 0; index4 < width / 8; ++index4)
            {
              for (int index5 = 0; index5 < 64; ++index5)
              {
                int num1 = TextureDecoder.tileOrder[index5] % 8;
                int num2 = (TextureDecoder.tileOrder[index5] - num1) / 8;
                long num3 = (long) ((index4 * 8 + num1 + (index3 * 8 + num2) * width) * 4);
                Buffer.BlockCopy((Array) data, (int) index1 + 1, (Array) numArray1, (int) num3, 3);
                numArray1[num3 + 3L] = data[index1];
                index1 += 4L;
              }
            }
          }
          break;
        case TextureFormat.RGB8:
          for (int index3 = 0; index3 < height / 8; ++index3)
          {
            for (int index4 = 0; index4 < width / 8; ++index4)
            {
              for (int index5 = 0; index5 < 64; ++index5)
              {
                int num1 = TextureDecoder.tileOrder[index5] % 8;
                int num2 = (TextureDecoder.tileOrder[index5] - num1) / 8;
                long num3 = (long) ((index4 * 8 + num1 + (index3 * 8 + num2) * width) * 4);
                Buffer.BlockCopy((Array) data, (int) index1, (Array) numArray1, (int) num3, 3);
                numArray1[num3 + 3L] = byte.MaxValue;
                index1 += 3L;
              }
            }
          }
          break;
        case TextureFormat.A8:
          for (int index3 = 0; index3 < height / 8; ++index3)
          {
            for (int index4 = 0; index4 < width / 8; ++index4)
            {
              for (int index5 = 0; index5 < 64; ++index5)
              {
                int num1 = TextureDecoder.tileOrder[index5] % 8;
                int num2 = (TextureDecoder.tileOrder[index5] - num1) / 8;
                long index6 = (long) ((index4 * 8 + num1 + (index3 * 8 + num2) * width) * 4);
                numArray1[index6] = byte.MaxValue;
                numArray1[index6 + 1L] = byte.MaxValue;
                numArray1[index6 + 2L] = byte.MaxValue;
                numArray1[index6 + 3L] = data[index1];
                ++index1;
              }
            }
          }
          break;
        case TextureFormat.L8:
          for (int index3 = 0; index3 < height / 8; ++index3)
          {
            for (int index4 = 0; index4 < width / 8; ++index4)
            {
              for (int index5 = 0; index5 < 64; ++index5)
              {
                int num1 = TextureDecoder.tileOrder[index5] % 8;
                int num2 = (TextureDecoder.tileOrder[index5] - num1) / 8;
                long index6 = (long) ((index4 * 8 + num1 + (index3 * 8 + num2) * width) * 4);
                numArray1[index6] = data[index1];
                numArray1[index6 + 1L] = data[index1];
                numArray1[index6 + 2L] = data[index1];
                numArray1[index6 + 3L] = byte.MaxValue;
                ++index1;
              }
            }
          }
          break;
        case TextureFormat.LA8:
          for (int index3 = 0; index3 < height / 8; ++index3)
          {
            for (int index4 = 0; index4 < width / 8; ++index4)
            {
              for (int index5 = 0; index5 < 64; ++index5)
              {
                int num1 = TextureDecoder.tileOrder[index5] % 8;
                int num2 = (TextureDecoder.tileOrder[index5] - num1) / 8;
                long index6 = (long) ((index4 * 8 + num1 + (index3 * 8 + num2) * width) * 4);
                numArray1[index6] = data[index1];
                numArray1[index6 + 1L] = data[index1];
                numArray1[index6 + 2L] = data[index1];
                numArray1[index6 + 3L] = data[index1 + 1L];
                index1 += 2L;
              }
            }
          }
          break;
        case TextureFormat.LA4:
          for (int index3 = 0; index3 < height / 8; ++index3)
          {
            for (int index4 = 0; index4 < width / 8; ++index4)
            {
              for (int index5 = 0; index5 < 64; ++index5)
              {
                int num1 = TextureDecoder.tileOrder[index5] % 8;
                int num2 = (TextureDecoder.tileOrder[index5] - num1) / 8;
                long index6 = (long) ((index4 * 8 + num1 + (index3 * 8 + num2) * width) * 4);
                numArray1[index6] = (byte) ((uint) data[index1] >> 4);
                numArray1[index6 + 1L] = (byte) ((uint) data[index1] >> 4);
                numArray1[index6 + 2L] = (byte) ((uint) data[index1] >> 4);
                numArray1[index6 + 3L] = (byte) ((uint) data[index1] & 15U);
                ++index1;
              }
            }
          }
          break;
        case TextureFormat.L4:
          for (int index3 = 0; index3 < height / 8; ++index3)
          {
            for (int index4 = 0; index4 < width / 8; ++index4)
            {
              for (int index5 = 0; index5 < 64; ++index5)
              {
                int num1 = TextureDecoder.tileOrder[index5] % 8;
                int num2 = (TextureDecoder.tileOrder[index5] - num1) / 8;
                long index6 = (long) ((index4 * 8 + num1 + (index3 * 8 + num2) * width) * 4);
                byte num3 = flag ? (byte) (((int) data[(IntPtr) index1++] & 240) >> 4) : (byte) ((uint) data[index1] & 15U);
                flag = !flag;
                byte num4 = (byte) ((uint) num3 << 4 | (uint) num3);
                numArray1[index6] = num4;
                numArray1[index6 + 1L] = num4;
                numArray1[index6 + 2L] = num4;
                numArray1[index6 + 3L] = byte.MaxValue;
              }
            }
          }
          break;
        case TextureFormat.RGBA4:
          for (int index3 = 0; index3 < height / 8; ++index3)
          {
            for (int index4 = 0; index4 < width / 8; ++index4)
            {
              for (int index5 = 0; index5 < 64; ++index5)
              {
                int num1 = TextureDecoder.tileOrder[index5] % 8;
                int num2 = (TextureDecoder.tileOrder[index5] - num1) / 8;
                long index6 = (long) ((index4 * 8 + num1 + (index3 * 8 + num2) * width) * 4);
                int num3 = (int) (ushort) ((uint) data[index1] | (uint) data[index1 + 1L] << 8);
                byte num4 = (byte) (num3 >> 4 & 15);
                byte num5 = (byte) (num3 >> 8 & 15);
                byte num6 = (byte) (num3 >> 12 & 15);
                byte num7 = (byte) (num3 & 15);
                numArray1[index6] = (byte) ((uint) num4 | (uint) num4 << 4);
                numArray1[index6 + 1L] = (byte) ((uint) num5 | (uint) num5 << 4);
                numArray1[index6 + 2L] = (byte) ((uint) num6 | (uint) num6 << 4);
                numArray1[index6 + 3L] = (byte) ((uint) num7 | (uint) num7 << 4);
                index1 += 2L;
              }
            }
          }
          break;
        case TextureFormat.RGBA5551:
          for (int index3 = 0; index3 < height / 8; ++index3)
          {
            for (int index4 = 0; index4 < width / 8; ++index4)
            {
              for (int index5 = 0; index5 < 64; ++index5)
              {
                int num1 = TextureDecoder.tileOrder[index5] % 8;
                int num2 = (TextureDecoder.tileOrder[index5] - num1) / 8;
                long index6 = (long) ((index4 * 8 + num1 + (index3 * 8 + num2) * width) * 4);
                int num3 = (int) (ushort) ((uint) data[index1] | (uint) data[index1 + 1L] << 8);
                byte num4 = (byte) ((num3 >> 1 & 31) << 3);
                byte num5 = (byte) ((num3 >> 6 & 31) << 3);
                byte num6 = (byte) ((num3 >> 11 & 31) << 3);
                byte num7 = (byte) ((num3 & 1) * (int) byte.MaxValue);
                numArray1[index6] = (byte) ((uint) num4 | (uint) num4 >> 5);
                numArray1[index6 + 1L] = (byte) ((uint) num5 | (uint) num5 >> 5);
                numArray1[index6 + 2L] = (byte) ((uint) num6 | (uint) num6 >> 5);
                numArray1[index6 + 3L] = num7;
                index1 += 2L;
              }
            }
          }
          break;
        case TextureFormat.RGB565:
          for (int index3 = 0; index3 < height / 8; ++index3)
          {
            for (int index4 = 0; index4 < width / 8; ++index4)
            {
              for (int index5 = 0; index5 < 64; ++index5)
              {
                int num1 = TextureDecoder.tileOrder[index5] % 8;
                int num2 = (TextureDecoder.tileOrder[index5] - num1) / 8;
                long index6 = (long) ((index4 * 8 + num1 + (index3 * 8 + num2) * width) * 4);
                int num3 = (int) (ushort) ((uint) data[index1] | (uint) data[index1 + 1L] << 8);
                byte num4 = (byte) ((num3 & 31) << 3);
                byte num5 = (byte) ((num3 >> 5 & 63) << 2);
                byte num6 = (byte) ((num3 >> 11 & 31) << 3);
                numArray1[index6] = (byte) ((uint) num4 | (uint) num4 >> 5);
                numArray1[index6 + 1L] = (byte) ((uint) num5 | (uint) num5 >> 6);
                numArray1[index6 + 2L] = (byte) ((uint) num6 | (uint) num6 >> 5);
                numArray1[index6 + 3L] = byte.MaxValue;
                index1 += 2L;
              }
            }
          }
          break;
      }
      return TextureDecoder.getBitmap(((IEnumerable<byte>) numArray1).ToArray<byte>(), width, height);
    }

    private static Bitmap getBitmap(byte[] array, int width, int height)
    {
      Bitmap bitmap = new Bitmap(width, height, PixelFormat.Format32bppArgb);
      BitmapData bitmapdata = bitmap.LockBits(new Rectangle(0, 0, bitmap.Width, bitmap.Height), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
      Marshal.Copy(array, 0, bitmapdata.Scan0, array.Length);
      bitmap.UnlockBits(bitmapdata);
      return bitmap;
    }

    private static byte[] etc1Decode(byte[] input, int width, int height, bool alpha)
    {
      byte[] numArray1 = new byte[width * height * 4];
      long num1 = 0;
      for (int index1 = 0; index1 < height / 4; ++index1)
      {
        for (int index2 = 0; index2 < width / 4; ++index2)
        {
          byte[] data = new byte[8];
          byte[] numArray2 = new byte[8];
          if (alpha)
          {
            for (int index3 = 0; index3 < 8; ++index3)
            {
              data[7 - index3] = input[num1 + 8L + (long) index3];
              numArray2[index3] = input[num1 + (long) index3];
            }
            num1 += 16L;
          }
          else
          {
            for (int index3 = 0; index3 < 8; ++index3)
            {
              data[7 - index3] = input[num1 + (long) index3];
              numArray2[index3] = byte.MaxValue;
            }
            num1 += 8L;
          }
          byte[] numArray3 = TextureDecoder.etc1DecodeBlock(data);
          bool flag = false;
          long index4 = 0;
          for (int index3 = 0; index3 < 4; ++index3)
          {
            for (int index5 = 0; index5 < 4; ++index5)
            {
              int dstOffset = (index2 * 4 + index3 + (index1 * 4 + index5) * width) * 4;
              int srcOffset = (index3 + index5 * 4) * 4;
              Buffer.BlockCopy((Array) numArray3, srcOffset, (Array) numArray1, dstOffset, 3);
              byte num2 = flag ? (byte) (((int) numArray2[(IntPtr) index4++] & 240) >> 4) : (byte) ((uint) numArray2[index4] & 15U);
              numArray1[dstOffset + 3] = (byte) ((uint) num2 << 4 | (uint) num2);
              flag = !flag;
            }
          }
        }
      }
      return numArray1;
    }

    private static byte[] etc1DecodeBlock(byte[] data)
    {
      uint uint32_1 = BitConverter.ToUInt32(data, 0);
      uint uint32_2 = BitConverter.ToUInt32(data, 4);
      int num1 = (uint32_1 & 16777216U) > 0U ? 1 : 0;
      uint r1;
      uint g1;
      uint b1;
      uint r2;
      uint g2;
      uint b2;
      if ((uint32_1 & 33554432U) > 0U)
      {
        uint num2 = uint32_1 & 248U;
        uint num3 = (uint32_1 & 63488U) >> 8;
        uint num4 = (uint32_1 & 16252928U) >> 16;
        uint num5 = (uint) (sbyte) (num2 >> 3) + ((uint) (sbyte) (((int) uint32_1 & 7) << 5) >> 5);
        uint num6 = (uint) (sbyte) (num3 >> 3) + ((uint) (sbyte) ((uint32_1 & 1792U) >> 3) >> 5);
        uint num7 = (uint) (sbyte) (num4 >> 3) + ((uint) (sbyte) ((uint32_1 & 458752U) >> 11) >> 5);
        r1 = num2 | num2 >> 5;
        g1 = num3 | num3 >> 5;
        b1 = num4 | num4 >> 5;
        r2 = num5 << 3 | num5 >> 2;
        g2 = num6 << 3 | num6 >> 2;
        b2 = num7 << 3 | num7 >> 2;
      }
      else
      {
        uint num2 = uint32_1 & 240U;
        uint num3 = (uint32_1 & 61440U) >> 8;
        uint num4 = (uint32_1 & 15728640U) >> 16;
        uint num5 = (uint) (((int) uint32_1 & 15) << 4);
        uint num6 = (uint32_1 & 3840U) >> 4;
        uint num7 = (uint32_1 & 983040U) >> 12;
        r1 = num2 | num2 >> 4;
        g1 = num3 | num3 >> 4;
        b1 = num4 | num4 >> 4;
        r2 = num5 | num5 >> 4;
        g2 = num6 | num6 >> 4;
        b2 = num7 | num7 >> 4;
      }
      uint table1 = uint32_1 >> 29 & 7U;
      uint table2 = uint32_1 >> 26 & 7U;
      byte[] numArray = new byte[64];
      if (num1 == 0)
      {
        for (int y = 0; y <= 3; ++y)
        {
          for (int x = 0; x <= 1; ++x)
          {
            Color color1 = TextureDecoder.etc1Pixel(r1, g1, b1, x, y, uint32_2, table1);
            Color color2 = TextureDecoder.etc1Pixel(r2, g2, b2, x + 2, y, uint32_2, table2);
            int index1 = (y * 4 + x) * 4;
            numArray[index1] = color1.B;
            numArray[index1 + 1] = color1.G;
            numArray[index1 + 2] = color1.R;
            int index2 = (y * 4 + x + 2) * 4;
            numArray[index2] = color2.B;
            numArray[index2 + 1] = color2.G;
            numArray[index2 + 2] = color2.R;
          }
        }
      }
      else
      {
        for (int y = 0; y <= 1; ++y)
        {
          for (int x = 0; x <= 3; ++x)
          {
            Color color1 = TextureDecoder.etc1Pixel(r1, g1, b1, x, y, uint32_2, table1);
            Color color2 = TextureDecoder.etc1Pixel(r2, g2, b2, x, y + 2, uint32_2, table2);
            int index1 = (y * 4 + x) * 4;
            numArray[index1] = color1.B;
            numArray[index1 + 1] = color1.G;
            numArray[index1 + 2] = color1.R;
            int index2 = ((y + 2) * 4 + x) * 4;
            numArray[index2] = color2.B;
            numArray[index2 + 1] = color2.G;
            numArray[index2 + 2] = color2.R;
          }
        }
      }
      return numArray;
    }

    private static Color etc1Pixel(
      uint r,
      uint g,
      uint b,
      int x,
      int y,
      uint block,
      uint table)
    {
      int num1 = x * 4 + y;
      uint num2 = block << 1;
      int num3 = num1 < 8 ? TextureDecoder.etc1LUT[(int) table, ((int) (block >> num1 + 24) & 1) + ((int) (num2 >> num1 + 8) & 2)] : TextureDecoder.etc1LUT[(int) table, ((int) (block >> num1 + 8) & 1) + ((int) (num2 >> num1 - 8) & 2)];
      r = (uint) TextureDecoder.saturate((int) ((long) r + (long) num3));
      g = (uint) TextureDecoder.saturate((int) ((long) g + (long) num3));
      b = (uint) TextureDecoder.saturate((int) ((long) b + (long) num3));
      return Color.FromArgb((int) r, (int) g, (int) b);
    }

    private static byte saturate(int value)
    {
      if (value > (int) byte.MaxValue)
        return byte.MaxValue;
      return value < 0 ? (byte) 0 : (byte) (value & (int) byte.MaxValue);
    }

    private static int[] etc1Scramble(int width, int height)
    {
      int[] numArray = new int[width / 4 * (height / 4)];
      int num1 = 0;
      int num2 = 0;
      int num3 = 0;
      int num4 = 0;
      for (int index = 0; index < numArray.Length; ++index)
      {
        if (index % (width / 4) == 0 && index > 0)
        {
          if (num2 < 1)
          {
            ++num2;
            num4 += 2;
            num3 = num4;
          }
          else
          {
            num2 = 0;
            num3 -= 2;
            num4 = num3;
          }
        }
        numArray[index] = num3;
        if (num1 < 1)
        {
          ++num1;
          ++num3;
        }
        else
        {
          num1 = 0;
          num3 += 3;
        }
      }
      return numArray;
    }
  }
}
