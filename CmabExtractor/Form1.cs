// Decompiled with JetBrains decompiler
// Type: CMABExtractor.Form1
// Assembly: CMABExtractor, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null
// MVID: F31EBCCA-BB47-4828-8339-39147FE028DD
// Assembly location: R:\Documents\PythonWorkspace\OoT3D-Importer\test_data\CMABExtractor.exe

using CMABExtractor.Properties;
using System;
using System.ComponentModel;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Windows.Forms;

namespace CMABExtractor
{
  public class Form1 : Form
  {
    private CMAB CmabEntries;
    private string FilePath;
    private IContainer components;
    private MenuStrip menuStrip1;
    private ToolStripMenuItem fileToolStripMenuItem;
    private ToolStripMenuItem eToolStripMenuItem;
    private ToolStripMenuItem openFileToolStripMenuItem;
    private ToolStripSeparator toolStripSeparator1;
    private OpenFileDialog openFileDialog1;
    private SplitContainer splitContainer1;
    private ListBox listBox1;
    private PictureBox pictureBox1;
    private StatusStrip statusStrip1;
    private ToolStripStatusLabel toolStripStatusLabel1;
    private ToolStripMenuItem actionsToolStripMenuItem;
    private ToolStripMenuItem extractCurrentToolStripMenuItem;
    private ToolStripMenuItem extractAllTexturesToolStripMenuItem;
    private SaveFileDialog saveFileDialog1;
    private FolderBrowserDialog folderBrowserDialog1;

    public Form1()
    {
      this.InitializeComponent();
    }

    private void exitToolStripMenuItem_Click(object sender, EventArgs e)
    {
      Application.Exit();
    }

    private void openFileToolStripMenuItem_Click(object sender, EventArgs e)
    {
      if (this.openFileDialog1.ShowDialog() != DialogResult.OK)
        return;
      this.listBox1.Items.Clear();
      this.FilePath = this.toolStripStatusLabel1.Text = this.openFileDialog1.FileName;
      this.CmabEntries = new CMAB(this.FilePath);
      foreach (CMABFile file in this.CmabEntries.Files)
        this.listBox1.Items.Add((object) string.Format("{0} - {1}", (object) file.Name, (object) TextureDecoder.GetFormat(file.Format)));
      this.listBox1.SelectedIndex = 0;
      this.actionsToolStripMenuItem.Enabled = true;
    }

    private void listBox1_SelectedIndexChanged(object sender, EventArgs e)
    {
      string entryName = this.listBox1.SelectedItem.ToString().Split('-')[0].TrimEnd();
      CMABFile cmabFile = this.CmabEntries.Files.FirstOrDefault<CMABFile>((Func<CMABFile, bool>) (item => item.Name == entryName));
      using (FileStream fileStream = new FileStream(this.FilePath, FileMode.Open, FileAccess.Read))
      {
        fileStream.Seek((long) cmabFile.Offset, SeekOrigin.Begin);
        byte[] numArray = new byte[cmabFile.Size];
        fileStream.Read(numArray, 0, numArray.Length);
        this.pictureBox1.Image = (Image) TextureDecoder.Decode(numArray, (int) cmabFile.Width, (int) cmabFile.Height, TextureDecoder.GetFormat(cmabFile.Format));
      }
    }

    private void extractCurrentToolStripMenuItem_Click(object sender, EventArgs e)
    {
      string str = this.listBox1.SelectedItem.ToString().Split('-')[0].TrimEnd();
      this.saveFileDialog1.FileName = str;
      if (this.saveFileDialog1.ShowDialog() != DialogResult.OK)
        return;
      this.pictureBox1.Image.Save(this.saveFileDialog1.FileName, ImageFormat.Png);
      int num = (int) MessageBox.Show(string.Format("'{0}' extracted!", (object) str), "CMABExtractor - Done", MessageBoxButtons.OK, MessageBoxIcon.Asterisk, MessageBoxDefaultButton.Button1);
    }

    private void extractAllTexturesToolStripMenuItem_Click(object sender, EventArgs e)
    {
      if (this.folderBrowserDialog1.ShowDialog() != DialogResult.OK)
        return;
      int selectedIndex = this.listBox1.SelectedIndex;
      for (int index = 0; index < this.listBox1.Items.Count; ++index)
      {
        this.listBox1.SelectedIndex = index;
        this.pictureBox1.Image.Save(Path.Combine(this.folderBrowserDialog1.SelectedPath, string.Format("{0}.png", (object) this.listBox1.SelectedItem.ToString().Split('-')[0].TrimEnd())), ImageFormat.Png);
      }
      this.listBox1.SelectedIndex = selectedIndex;
      int num = (int) MessageBox.Show(string.Format("'{0}' fully extracted!", (object) Path.GetFileName(this.toolStripStatusLabel1.Text)), "CMABExtractor - Done", MessageBoxButtons.OK, MessageBoxIcon.Asterisk, MessageBoxDefaultButton.Button1);
    }

    protected override void Dispose(bool disposing)
    {
      if (disposing && this.components != null)
        this.components.Dispose();
      base.Dispose(disposing);
    }

    private void InitializeComponent()
    {
      ComponentResourceManager componentResourceManager = new ComponentResourceManager(typeof (Form1));
      this.menuStrip1 = new MenuStrip();
      this.openFileDialog1 = new OpenFileDialog();
      this.splitContainer1 = new SplitContainer();
      this.listBox1 = new ListBox();
      this.statusStrip1 = new StatusStrip();
      this.toolStripStatusLabel1 = new ToolStripStatusLabel();
      this.saveFileDialog1 = new SaveFileDialog();
      this.folderBrowserDialog1 = new FolderBrowserDialog();
      this.pictureBox1 = new PictureBox();
      this.fileToolStripMenuItem = new ToolStripMenuItem();
      this.openFileToolStripMenuItem = new ToolStripMenuItem();
      this.toolStripSeparator1 = new ToolStripSeparator();
      this.eToolStripMenuItem = new ToolStripMenuItem();
      this.actionsToolStripMenuItem = new ToolStripMenuItem();
      this.extractCurrentToolStripMenuItem = new ToolStripMenuItem();
      this.extractAllTexturesToolStripMenuItem = new ToolStripMenuItem();
      this.menuStrip1.SuspendLayout();
      this.splitContainer1.BeginInit();
      this.splitContainer1.Panel1.SuspendLayout();
      this.splitContainer1.Panel2.SuspendLayout();
      this.splitContainer1.SuspendLayout();
      this.statusStrip1.SuspendLayout();
      ((ISupportInitialize) this.pictureBox1).BeginInit();
      this.SuspendLayout();
      this.menuStrip1.Items.AddRange(new ToolStripItem[2]
      {
        (ToolStripItem) this.fileToolStripMenuItem,
        (ToolStripItem) this.actionsToolStripMenuItem
      });
      this.menuStrip1.Location = new Point(0, 0);
      this.menuStrip1.Name = "menuStrip1";
      this.menuStrip1.Size = new Size(520, 24);
      this.menuStrip1.TabIndex = 0;
      this.menuStrip1.Text = "menuStrip1";
      this.openFileDialog1.FileName = "openFileDialog1";
      this.openFileDialog1.Filter = "CMAB Files|*.cmab|All Files|*.*";
      this.splitContainer1.Dock = DockStyle.Fill;
      this.splitContainer1.Location = new Point(0, 24);
      this.splitContainer1.Name = "splitContainer1";
      this.splitContainer1.Panel1.Controls.Add((Control) this.listBox1);
      this.splitContainer1.Panel2.BackgroundImage = (Image) Resources.transparent;
      this.splitContainer1.Panel2.Controls.Add((Control) this.pictureBox1);
      this.splitContainer1.Size = new Size(520, 244);
      this.splitContainer1.SplitterDistance = 173;
      this.splitContainer1.TabIndex = 1;
      this.listBox1.Dock = DockStyle.Fill;
      this.listBox1.FormattingEnabled = true;
      this.listBox1.Location = new Point(0, 0);
      this.listBox1.Name = "listBox1";
      this.listBox1.Size = new Size(173, 244);
      this.listBox1.TabIndex = 0;
      this.listBox1.SelectedIndexChanged += new EventHandler(this.listBox1_SelectedIndexChanged);
      this.statusStrip1.Items.AddRange(new ToolStripItem[1]
      {
        (ToolStripItem) this.toolStripStatusLabel1
      });
      this.statusStrip1.Location = new Point(0, 268);
      this.statusStrip1.Name = "statusStrip1";
      this.statusStrip1.Size = new Size(520, 22);
      this.statusStrip1.TabIndex = 2;
      this.statusStrip1.Text = "statusStrip1";
      this.toolStripStatusLabel1.Name = "toolStripStatusLabel1";
      this.toolStripStatusLabel1.Size = new Size(0, 17);
      this.saveFileDialog1.Filter = "PNG File|*.png";
      this.pictureBox1.BackColor = Color.Transparent;
      this.pictureBox1.Location = new Point(2, 3);
      this.pictureBox1.Name = "pictureBox1";
      this.pictureBox1.Size = new Size(50, 36);
      this.pictureBox1.SizeMode = PictureBoxSizeMode.AutoSize;
      this.pictureBox1.TabIndex = 0;
      this.pictureBox1.TabStop = false;
      this.fileToolStripMenuItem.DropDownItems.AddRange(new ToolStripItem[3]
      {
        (ToolStripItem) this.openFileToolStripMenuItem,
        (ToolStripItem) this.toolStripSeparator1,
        (ToolStripItem) this.eToolStripMenuItem
      });
      this.fileToolStripMenuItem.Image = (Image) Resources.page_white_text;
      this.fileToolStripMenuItem.Name = "fileToolStripMenuItem";
      this.fileToolStripMenuItem.Size = new Size(53, 20);
      this.fileToolStripMenuItem.Text = "File";
      this.openFileToolStripMenuItem.Image = (Image) Resources.folder_page;
      this.openFileToolStripMenuItem.Name = "openFileToolStripMenuItem";
      this.openFileToolStripMenuItem.Size = new Size(124, 22);
      this.openFileToolStripMenuItem.Text = "Open File";
      this.openFileToolStripMenuItem.Click += new EventHandler(this.openFileToolStripMenuItem_Click);
      this.toolStripSeparator1.Name = "toolStripSeparator1";
      this.toolStripSeparator1.Size = new Size(121, 6);
      this.eToolStripMenuItem.Image = (Image) Resources.cancel;
      this.eToolStripMenuItem.Name = "eToolStripMenuItem";
      this.eToolStripMenuItem.Size = new Size(124, 22);
      this.eToolStripMenuItem.Text = "Exit";
      this.eToolStripMenuItem.Click += new EventHandler(this.exitToolStripMenuItem_Click);
      this.actionsToolStripMenuItem.DropDownItems.AddRange(new ToolStripItem[2]
      {
        (ToolStripItem) this.extractCurrentToolStripMenuItem,
        (ToolStripItem) this.extractAllTexturesToolStripMenuItem
      });
      this.actionsToolStripMenuItem.Enabled = false;
      this.actionsToolStripMenuItem.Image = (Image) Resources.server_go;
      this.actionsToolStripMenuItem.Name = "actionsToolStripMenuItem";
      this.actionsToolStripMenuItem.Size = new Size(75, 20);
      this.actionsToolStripMenuItem.Text = "Actions";
      this.extractCurrentToolStripMenuItem.Image = (Image) Resources.picture;
      this.extractCurrentToolStripMenuItem.Name = "extractCurrentToolStripMenuItem";
      this.extractCurrentToolStripMenuItem.Size = new Size(193, 22);
      this.extractCurrentToolStripMenuItem.Text = "Extract Current Texture";
      this.extractCurrentToolStripMenuItem.Click += new EventHandler(this.extractCurrentToolStripMenuItem_Click);
      this.extractAllTexturesToolStripMenuItem.Image = (Image) Resources.pictures;
      this.extractAllTexturesToolStripMenuItem.Name = "extractAllTexturesToolStripMenuItem";
      this.extractAllTexturesToolStripMenuItem.Size = new Size(193, 22);
      this.extractAllTexturesToolStripMenuItem.Text = "Extract All Textures";
      this.extractAllTexturesToolStripMenuItem.Click += new EventHandler(this.extractAllTexturesToolStripMenuItem_Click);
      this.AutoScaleDimensions = new SizeF(6f, 13f);
      this.AutoScaleMode = AutoScaleMode.Font;
      this.ClientSize = new Size(520, 290);
      this.Controls.Add((Control) this.splitContainer1);
      this.Controls.Add((Control) this.menuStrip1);
      this.Controls.Add((Control) this.statusStrip1);
      this.Icon = (Icon) componentResourceManager.GetObject("$this.Icon");
      this.MainMenuStrip = this.menuStrip1;
      this.Name = nameof (Form1);
      this.StartPosition = FormStartPosition.CenterScreen;
      this.Text = "CMABExtractor v0.1 by Ac_K";
      this.menuStrip1.ResumeLayout(false);
      this.menuStrip1.PerformLayout();
      this.splitContainer1.Panel1.ResumeLayout(false);
      this.splitContainer1.Panel2.ResumeLayout(false);
      this.splitContainer1.Panel2.PerformLayout();
      this.splitContainer1.EndInit();
      this.splitContainer1.ResumeLayout(false);
      this.statusStrip1.ResumeLayout(false);
      this.statusStrip1.PerformLayout();
      ((ISupportInitialize) this.pictureBox1).EndInit();
      this.ResumeLayout(false);
      this.PerformLayout();
    }
  }
}
